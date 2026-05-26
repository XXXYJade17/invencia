# 03 —— 角色模块详细设计

> 版本：v3.1
> 日期：2026-05-25
> 依赖：01-database.md、05-dify-workflows.md
> 角色模板：[xuantian-realm/02-char-template.md](./xuantian-realm/02-char-template.md)
>
> **v3.1 变更**：灵根移除，新增 combat_rating 道韵字段，境界重设，分级对齐。
**v3.0 变更**：角色信息结构升级为新模板（"标签——描述"格式），合并算法适配新结构。
> **v2.1 变更**：infomation.cultivation 增加 spiritual_roots 字段。
> **v2.0 变更**：infomation 升级为分层结构 + 数组字段。

---

## 一、角色 CRUD 实现

### 1.1 查询角色列表

```python
def list_characters(user_id, world_id=None):
    with get_db() as conn:
        sql = "SELECT id, name, gender, world_id, is_dead, created_at FROM characters WHERE user_id = ? AND del_flag = 0"
        params = [user_id]
        if world_id:
            sql += " AND world_id = ?"
            params.append(world_id)
        rows = conn.execute(sql + " ORDER BY created_at DESC", params).fetchall()
    return [dict(r) for r in rows]
```

### 1.2 查询角色详情

```python
def get_character(character_id, user_id):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM characters WHERE id = ? AND user_id = ? AND del_flag = 0",
            (character_id, user_id)
        ).fetchone()
    if not row:
        return None
    ch = dict(row)
    ch["infomation"] = json.loads(ch["infomation"])
    return ch
```

### 1.3 删除角色

```python
def delete_character(character_id, user_id):
    with get_db() as conn:
        cur = conn.execute(
            "UPDATE characters SET del_flag = 1 WHERE id = ? AND user_id = ? AND del_flag = 0",
            (character_id, user_id)
        )
        if cur.rowcount == 0:
            return False
        conn.execute("UPDATE messages SET del_flag = 1 WHERE character_id = ?", (character_id,))
    return True
```

---

## 二、角色创建（AI 生成编排）

### 2.1 流程

```
POST /api/characters {name, gender, world_id}
  → 校验角色数量上限（3个）
    → 读取 world_config 获取世界信息
      → 读取 prompts/char_create.txt 并填充变量
        → 调用 Dify 工作流（system_prompt 作为参数传入）
          → Dify 返回角色信息 JSON
            → 后端 verify_character_data() 校验结构
              → 写入数据库
                → 返回 201 + 完整角色数据
```

### 2.2 角色信息结构校验

> 完整结构定义见 [xuantian-realm/02-char-template.md](./xuantian-realm/02-char-template.md)。

```python
REQUIRED_TOP_FIELDS = [
    "name", "gender", "appearance", "background", "is_alive",
    "combat_rating", "cultivation", "items", "skills", "relationships"
]

ITEM_FIELDS = {"name", "category", "quantity", "grade", "effect", "condition"}
SKILL_FIELDS = {"name", "category", "grade", "effect", "progress"}
RELATIONSHIP_FIELDS = {"name", "identity", "description"}

def verify_character_data(data):
    """校验 AI 生成的角色信息结构完整性"""

    # 1. 顶层字段
    missing = [f for f in REQUIRED_TOP_FIELDS if f not in data]
    if missing:
        raise ValueError(f"Missing top-level fields: {missing}")

    # 2. 标量字段校验
    for f in ["appearance", "background"]:
        if not data.get(f) or len(data[f].strip()) < 60:
            raise ValueError(f"{f} too short or missing (min 60 chars)")

        # 3. combat_rating 校验
    cr = data["combat_rating"]
    if not cr or len(cr.strip()) < 40:
        raise ValueError("combat_rating too short or missing")
    if "——" not in cr:
        raise ValueError("combat_rating must follow 'label——description' format")
# 4. cultivation 校验
    cul = data["cultivation"]
    if not isinstance(cul, dict):
        raise ValueError("cultivation must be an object")
    for f in ["realm", "physique", "soul"]:
        if not cul.get(f) or len(cul[f].strip()) < 30:
            raise ValueError(f"cultivation.{f} too short or missing")
        if "——" not in cul[f]:
            raise ValueError(f"cultivation.{f} must follow 'label——description' format")

    # 5. items 校验（凡人创建时 ≥2 件）
    if not isinstance(data["items"], list) or len(data["items"]) < 2:
        raise ValueError("items must have at least 2 items")
    for item in data["items"]:
        missing_fields = ITEM_FIELDS - set(item.keys())
        if missing_fields:
            raise ValueError(f"item '{item.get('name', '?')}' missing fields: {missing_fields}")

    # 6. skills 校验
    if not isinstance(data["skills"], list):
        raise ValueError("skills must be an array")

    # 7. relationships 校验（≥1 人）
    if not isinstance(data["relationships"], list) or len(data["relationships"]) < 1:
        raise ValueError("relationships must have at least 1 person")
    for r in data["relationships"]:
        missing_fields = RELATIONSHIP_FIELDS - set(r.keys())
        if missing_fields:
            raise ValueError(f"relationship '{r.get('name', '?')}' missing fields: {missing_fields}")

    return True
```

---

## 三、角色信息合并算法

> 每次天道推演后，Agent 输出的 `info_changes` 与数据库中的角色信息合并。
>
> `info_changes` 结构定义见 [xuantian-realm/03-prompts.md](./xuantian-realm/03-prompts.md) §二（输出格式）。

### 3.1 合并总览

| 字段类型 | 字段 | 合并策略 | 说明 |
|----------|------|----------|------|
| **标量值** | name | 覆盖 | 极少变化 |
| **标量值** | gender | 覆盖 | 极少变化 |
| **标量值** | appearance | 覆盖 | 外貌变化时更新 |
| **标量值** | background | 覆盖 | 背景补充时更新 |
| **标量值** | is_alive | 覆盖 | 死亡时更新 |
| **标量对象** | talent | 覆盖 | spirit_root 或 constitutions 变化 → 覆盖整个对象 |
| **标量对象** | cultivation | 覆盖 | realm/physique/soul 任意变化 → 覆盖整个对象 |
| **数组** | items[] | **按 name 合并** | 同名更新；quantity 为 "无" 删除；新 name 追加 |
| **数组** | skills[] | **按 name 合并** | 同名更新 progress/effect；新 name 追加 |
| **数组** | relationships[] | **按 name 合并** | 同名更新 description；新 name 追加 |

### 3.2 标量覆盖

```python
SCALAR_KEYS = ["name", "gender", "appearance", "background", "is_alive",
               "combat_rating", "cultivation"]

def merge_scalar(current, changes):
    """标量字段直接覆盖"""
    for key in SCALAR_KEYS:
        if key in changes and changes[key] is not None:
            current[key] = changes[key]
    return current
```

### 3.3 数组合并

```python
def merge_array_by_name(current_list, changes_list, match_key="name"):
    """按 match_key 匹配合并两个数组。changes 中的条目覆盖 current 中的同名条目。"""
    current_map = {item[match_key]: item for item in current_list}

    for change in changes_list:
        key = change[match_key]

        # items 特殊处理：quantity 为 "无" 或空字符串表示删除
        if match_key == "name" and change.get("quantity", "").strip() in ("无", ""):
            current_map.pop(key, None)
        elif key in current_map:
            current_map[key].update(change)
        else:
            current_map[key] = change

    return list(current_map.values())
```

### 3.4 主合并函数

```python
def merge_character_data(current, info_changes):
    """将 info_changes 合并到 current 角色信息。不修改 current，返回新对象。"""
    import copy
    result = copy.deepcopy(current)

    if not info_changes:
        return result

    # 1. 标量覆盖
    merge_scalar(result, info_changes)

    # 2. 数组合并
    array_configs = [
        ("items", "name"),
        ("skills", "name"),
        ("relationships", "name"),
    ]
    for array_key, match_key in array_configs:
        if array_key in info_changes and isinstance(info_changes[array_key], list):
            result[array_key] = merge_array_by_name(
                result.get(array_key, []),
                info_changes[array_key],
                match_key
            )

    return result
```

### 3.5 使用示例

> 玩家捡到一把铁剑，消耗 1 块灵石。境界从凡人突破到炼气期。

```python
info_changes = {
    "cultivation": {
        "realm": "炼气境·一层——引气入体成功！丹田中第一缕真气如烛火般燃起...",
        "physique": "凡人之躯——常年山林中练就的体魄，如今在灵气滋养下开始蜕变...",
        "soul": "凡人神识——精神力比昨日敏锐了三分，闭眼时隐约能感知到三尺外树叶的晃动..."
    },
    "items": [
        {
            "name": "生锈铁剑",
            "category": "兵器",
            "quantity": "仅此一把——从妖兽巢穴里捡来",
            "grade": "下品",
            "effect": "比猎刀长一尺，剑身上锈迹斑斑但刃口尚利",
            "condition": "老旧——剑柄缠的麻绳快断了"
        },
        {
            "name": "下品灵石",
            "category": "材料",
            "quantity": "仅剩一块——原有两块，修炼时消耗了一块",
            "grade": "下品",
            "effect": "蕴含微弱灵气，可供炼气境武者补充灵力",
            "condition": "完好——微微泛着乳白色荧光"
        }
    ]
}
new_data = merge_character_data(current_data, info_changes)
# cultivation 整体覆盖 | items 中铁剑新增、灵石 qty 从两块变一块
```

### 3.6 降级处理

| 场景 | 处理 |
|------|------|
| info_changes 为 null 或 {} | 不做任何更新，角色信息保持不变 |
| 数组条目缺少 match_key | 跳过该条目，记录 warning 日志 |
| JSON 解析失败 | 降级：不更新角色信息，仅展示 narrative |
| info_changes 包含未知字段 | 忽略（不在 SCALAR_KEYS 或 array_configs 中的字段） |

---

## 四、角色面板更新

```python
def update_character(character_id, user_id, data):
    allowed = {"name", "gender", "infomation"}
    updates = {k: v for k, v in data.items() if k in allowed}
    if not updates:
        return get_character(character_id, user_id)

    if "infomation" in updates:
        updates["infomation"] = json.dumps(updates["infomation"], ensure_ascii=False)

    set_clause = ", ".join(f"{k}=?" for k in updates)
    values = list(updates.values()) + [character_id, user_id]

    with get_db() as conn:
        cur = conn.execute(
            f"UPDATE characters SET {set_clause}, updated_at=datetime('now','localtime') WHERE id=? AND user_id=? AND del_flag=0",
            values
        )
        if cur.rowcount == 0:
            return None

    return get_character(character_id, user_id)
```

---

*03-characters.md v3.0。下一步：[04-game-engine.md](./04-game-engine.md)。*