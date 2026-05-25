# 03 —— 角色模块详细设计
> 版本：v2.1
> 日期：2026-05-25
> 依赖：01-database.md、05-dify-workflows.md
> **v2.1 变更**：infomation.cultivation 增加 spiritual_roots 字段（初始空数组，灵根觉醒后填充）。**v2.0 变更**：infomation 升级为分层结构 + 数组字段。merge 算法重写。
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
          → Dify 返回 infomation JSON
            → 后端 verify_infomation() 校验结构
              → 写入数据库
                → 返回 201 + 完整角色数据
```
### 2.2 infomation 结构校验
```python
REQUIRED_TOP_FIELDS = [
    "basic_info", "cultivation", "physique", "mind_spirit",
    "inventory", "techniques", "relationships", "causality",
    "location"
]
INVENTORY_FIELDS = {"name", "type", "grade", "quantity", "description"}
TECHNIQUE_FIELDS = {"name", "type", "mastery", "description"}
RELATIONSHIP_FIELDS = {"name", "identity", "relationship", "attitude", "notes"}
CAUSALITY_FIELDS = {"event", "description", "status"}
def verify_infomation(info):
    """校验 AI 生成的 infomation 结构完整性"""
    # 1. 顶层字段
    missing = [f for f in REQUIRED_TOP_FIELDS if f not in info]
    if missing:
        raise ValueError(f"Missing top-level fields: {missing}")
    # 2. basic_info 子字段
    bi = info["basic_info"]
    for f in ["appearance", "personality", "origin"]:
        if not bi.get(f) or len(bi[f].strip()) < 40:
            raise ValueError(f"basic_info.{f} too short or missing")
    # 3. cultivation 子字段
    cu = info["cultivation"]
    for f in ["realm", "power", "dao_heart"]:
        if not cu.get(f) or len(cu[f].strip()) < 30:
            raise ValueError(f"cultivation.{f} too short or missing")
    # 4. physique
    sr = cu.get("spiritual_roots")
    if sr is not None and not isinstance(sr, list):
        raise ValueError("cultivation.spiritual_roots must be a list")
    # 4. physique 子字段
    ph = info["physique"]
    if not ph.get("condition") or len(ph["condition"].strip()) < 30:
        raise ValueError("physique.condition too short")
    if not isinstance(ph.get("traits"), list):
        raise ValueError("physique.traits must be an array")
    # 5. mind_spirit 子字段
    ms = info["mind_spirit"]
    for f in ["mental_state", "spiritual_power"]:
        if not ms.get(f) or len(ms[f].strip()) < 20:
            raise ValueError(f"mind_spirit.{f} too short")
    # 6. 数组字段结构校验 + 数量校验
    if not isinstance(info["inventory"], list) or len(info["inventory"]) < 2:
        raise ValueError("inventory must have at least 2 items")
    for item in info["inventory"]:
        missing = INVENTORY_FIELDS - set(item.keys())
        if missing:
            raise ValueError(f"inventory item missing fields: {missing}")
    if not isinstance(info["techniques"], list):
        raise ValueError("techniques must be an array")
    for t in info["techniques"]:
        missing = TECHNIQUE_FIELDS - set(t.keys())
        if missing:
            raise ValueError(f"technique missing fields: {missing}")
    if not isinstance(info["relationships"], list) or len(info["relationships"]) < 1:
        raise ValueError("relationships must have at least 1 person")
    for r in info["relationships"]:
        missing = RELATIONSHIP_FIELDS - set(r.keys())
        if missing:
            raise ValueError(f"relationship missing fields: {missing}")
    if not isinstance(info["causality"], list) or len(info["causality"]) < 1:
        raise ValueError("causality must have at least 1 entry")
    # 7. 标量字段
    for f in ["location"]:
        if not info.get(f) or len(info[f].strip()) < 10:
            raise ValueError(f"{f} too short")
    print("infomation verification passed")
```
### 2.3 create_character 核心实现
```python
MAX_CHARACTERS = 3
def create_character(user_id, name, gender, world_id):
    # 1. 校验上限
    with get_db() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM characters WHERE user_id = ? AND del_flag = 0",
            (user_id,)
---
## 二、角色创建（AI 生成编排）
### 2.1 流程
`
POST /api/characters {name, gender, world_id}
  -> 校验角色数量上限（3个）
    -> 读取 world_config 获取世界信息
      -> 读取 prompts/char_create.txt 并填充变量
        -> 调用 Dify 工作流（system_prompt 作为参数传入）
          -> Dify 返回 infomation JSON
            -> 后端 verify_infomation() 校验结构
              -> 写入数据库
                -> 返回 201 + 完整角色数据
`
---
## 二、角色创建（AI 生成编排）
### 2.1 流程
```
POST /api/characters {name, gender, world_id}
  -> 校验角色数量上限（3个）
    -> 读取 world_config 获取世界信息
      -> 读取 prompts/char_create.txt 并填充变量
        -> 调用 Dify 工作流（system_prompt 作为参数传入）
          -> Dify 返回 infomation JSON
            -> 后端 verify_infomation() 校验结构
              -> 写入数据库
                -> 返回 201 + 完整角色数据
```
### 2.2 infomation 结构校验（verify_infomation）
```python
REQUIRED_TOP_FIELDS = ["basic_info","cultivation","physique","mind_spirit",
    "inventory","techniques","relationships","causality","location"]
def verify_infomation(info):
    missing = [f for f in REQUIRED_TOP_FIELDS if f not in info]
    if missing: raise ValueError(f"Missing: {missing}")
    # basic_info
    for f in ["appearance","personality","origin"]:
        if not info["basic_info"].get(f) or len(info["basic_info"][f].strip()) < 40:
            raise ValueError(f"basic_info.{f} too short")
    # cultivation
    for f in ["realm","power","dao_heart"]:
        if not info["cultivation"].get(f) or len(info["cultivation"][f].strip()) < 30:
            raise ValueError(f"cultivation.{f} too short")
    # physique
    sr = info["cultivation"].get("spiritual_roots")
    if sr is not None and not isinstance(sr, list): raise ValueError("spiritual_roots not array")
    # physique
    if not info["physique"].get("condition"): raise ValueError("physique.condition missing")
    if not isinstance(info["physique"].get("traits"), list): raise ValueError("traits not array")
    # mind_spirit
    for f in ["mental_state","spiritual_power"]:
        if not info["mind_spirit"].get(f): raise ValueError(f"mind_spirit.{f} missing")
    # inventory (>=2 items, each with required fields)
    if not isinstance(info.get("inventory"), list) or len(info["inventory"]) < 2:
        raise ValueError("inventory must have >= 2 items")
    INV_FIELDS = {"name","type","grade","quantity","description"}
    for item in info["inventory"]:
        if INV_FIELDS - set(item.keys()): raise ValueError("inventory item missing fields")
    # techniques (may be empty, but if present each has required fields)
    if not isinstance(info.get("techniques"), list): raise ValueError("techniques not array")
    TECH_FIELDS = {"name","type","mastery","description"}
    for t in info["techniques"]:
        if TECH_FIELDS - set(t.keys()): raise ValueError("technique missing fields")
    # relationships (>=1)
    if not isinstance(info.get("relationships"), list) or len(info["relationships"]) < 1:
        raise ValueError("relationships must have >= 1 person")
    REL_FIELDS = {"name","identity","relationship","attitude","notes"}
    for r in info["relationships"]:
        if REL_FIELDS - set(r.keys()): raise ValueError("relationship missing fields")
    # causality (>=1)
    if not isinstance(info.get("causality"), list) or len(info["causality"]) < 1:
        raise ValueError("causality must have >= 1 entry")
    # scalar fields
    for f in ["location"]:
        if not info.get(f) or len(info[f].strip()) < 10:
            raise ValueError(f"{f} too short")
```
### 2.3 create_character 完整实现
```python
MAX_CHARACTERS = 3
def create_character(user_id, name, gender, world_id):
    # 1. 校验上限 + 获取世界信息
    with get_db() as conn:
        count = conn.execute("SELECT COUNT(*) FROM characters WHERE user_id=? AND del_flag=0",
                            (user_id,)).fetchone()[0]
        if count >= MAX_CHARACTERS:
            raise ValueError("角色数量已达上限")
        world = conn.execute("SELECT * FROM world_config WHERE id=?", (world_id,)).fetchone()
        if not world: raise ValueError("世界不存在")
    # 2. 读取 Prompt 模板并填充变量
    prompt = load_prompt("char_create.txt").format(
        world_name=world["display_name"],
        world_description=world["description"])
    # 3. 调用 Dify（Prompt 作为 system_prompt 参数传入工作流）
    result = call_workflow(workflow_type="character_creation", params={
        "char_name": name, "char_gender": gender, "system_prompt": prompt})
    infomation = json.loads(result["output"])
    # 4. 校验
    verify_infomation(infomation)
    # 5. 入库
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO characters (user_id,world_id,name,gender,infomation) VALUES (?,?,?,?,?)",
            (user_id, world_id, name, gender, json.dumps(infomation, ensure_ascii=False)))
        return get_character(cur.lastrowid, user_id)
def load_prompt(filename):
    path = os.path.join("prompts", filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()
```
---
## 三、infomation Merge 算法
> 每次天道推演返回 info_changes 后，需要将其合并到角色当前 infomation 中。新算法区分标量和数组两种更新策略。
### 3.1 更新策略总览
| 字段类型 | 字段 | 策略 | 说明 |
|----------|------|------|------|
| 标量对象 | basic_info | 覆盖 | 外貌/性格/身世极少变化，如有变化直接覆盖整个对象 |
| 标量对象 | cultivation | 覆盖 | realm/power/dao_heart/spiritual_roots 的任意变化 → 覆盖整个对象 |
| 标量对象 | physique | 覆盖 | condition 变化或 traits[] 变化 → 覆盖整个对象 |
| 标量对象 | mind_spirit | 覆盖 | mental_state/spiritual_power 变化 → 覆盖整个对象 |
| 标量值 | location | 覆盖 | 直接替换 |
| **数组** | inventory[] | **按 name 合并** | 同名更新 quantity/grade/description；quantity=0 删除；新 name 追加 |
| **数组** | techniques[] | **按 name 合并** | 同名更新 mastery/description；新 name 追加 |
| **数组** | relationships[] | **按 name 合并** | 同名更新 attitude/notes；新 name 追加 |
| **数组** | causality[] | **按 event 合并** | 同 event 更新 status/description；新 event 追加 |
### 3.2 标量覆盖
> 简单直接——info_changes 中出现了某个标量字段，就用新值替换旧值。未出现则保留原值。
```python
SCALAR_KEYS = ["basic_info","cultivation","physique","mind_spirit","location"]
def merge_scalar(current, changes):
    for key in SCALAR_KEYS:
        if key in changes and changes[key] is not None:
            current[key] = changes[key]
    return current
```
### 3.3 数组合并
> 核心逻辑：按 name（物品/功法/人际关系）或 event（因果）匹配 → 更新或追加。支持删除（inventory quantity=0）。
```python
def merge_array_by_name(current_list, changes_list, match_key="name"):
    """按 match_key 匹配合并两个数组。changes 中的条目覆盖 current 中的同名条目。"""
    current_map = {item[match_key]: item for item in current_list}
    for change in changes_list:
        key = change[match_key]
        # inventory 特殊处理：quantity=0 表示删除
        if match_key == "name" and change.get("quantity") == 0:
            current_map.pop(key, None)
        elif key in current_map:
            current_map[key].update(change)
        else:
            current_map[key] = change
    return list(current_map.values())
```
### 3.4 主合并函数
```python
def merge_infomation(current, info_changes):
    """将 info_changes 合并到 current infomation。不修改 current，返回新对象。"""
    import copy
    result = copy.deepcopy(current)
    if not info_changes:
        return result
    # 1. 标量覆盖
    merge_scalar(result, info_changes)
    # 2. 数组合并
    array_configs = [
        ("inventory", "name"),
        ("techniques", "name"),
        ("relationships", "name"),
        ("causality", "event")
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
> 玩家捡到一把铁剑，同时消耗 1 块灵石，道心被妖兽震慑后动摇。
```python
info_changes = {
    "cultivation": {"realm": "...(新)", "power": "...(新)", "dao_heart": "...(动摇)"},
    "inventory": [
        {"name": "生锈铁剑", "type": "weapon", "grade": "凡品", "quantity": 1,
         "description": "从妖兽巢穴里捡来的..."},
        {"name": "下品灵石", "type": "currency", "grade": "下品", "quantity": 1,
         "description": "原有2块，消耗1块"}
    ],
    "location": "苍玄域·黑风谷——妖兽巢穴外围..."
}
new_info = merge_infomation(current_info, info_changes)
# cultivation 整体覆盖 | inventory 新增铁剑、灵石 quantity 从2变1 | location 覆盖
```
### 3.6 降级处理
| 场景 | 处理 |
|------|------|
| info_changes 为 null 或 {} | 不做任何更新，infomation 保持不变 |
| 数组条目缺少 match_key | 跳过该条目，记录 warning 日志 |
| JSON 解析失败 | 降级：不更新 infomation，仅展示 narrative |
| info_changes 包含未知字段 | 忽略（不在 SCALAR_KEYS 或 array_configs 中的字段） |
---
## 四、角色面板更新
```python
def update_character(character_id, user_id, data):
    allowed = {"name","gender","infomation"}
    updates = {k:v for k,v in data.items() if k in allowed}
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
        if cur.rowcount == 0: return None
    return get_character(character_id, user_id)
```
---
*03-characters.md v2.0。下一步：[04-game-engine.md](./04-game-engine.md)。*