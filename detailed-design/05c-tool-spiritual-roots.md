# 05c —— 灵根觉醒工具设计

> 版本：v2.0
> 日期：2026-05-25
> 对应资源：Dify Tool `awaken-spiritual-roots`（Code Tool）
> 调用方：Dify Chatflow Agent 节点（天道推演时自主调用）
>
> **v2.0 变更**：从 Coze 代码节点切换为 Dify Code Tool，由 Agent 原生 function calling 触发。

---

## 一、工具注册（Dify 配置）

在 Dify 中注册为 **Code Tool**：

| 配置项 | 值 |
|--------|-----|
| 名称 | `awaken-spiritual-roots` |
| 类型 | Code Tool（Python） |
| 描述 | 觉醒角色的灵根。按概率表随机抽取灵根类型，返回灵根元素列表、类别、稀有度和叙事种子。仅在角色尚未觉醒灵根时调用。 |
| 输入参数 | |
| | `character_id` (number, required) — 角色 ID |
| | `character_name` (string, required) — 角色名 |
| | `infomation` (string, required) — 当前 infomation JSON 字符串 |
| 输出 | JSON |

---

## 二、工具实现

```python
import random
import json

# ============================================================
# 灵根概率表
# 格式: (类别, 灵根元素列表, 权重, 稀有度, 叙事种子)
# ============================================================
SPIRITUAL_ROOT_TABLE = [
    # ── 伪灵根（40%）──
    ("伪灵根", ["金","木","水","火","土"], 40, "common",
     "五行俱全却无一精纯，资质平庸，修炼速度远逊常人"),
    # ── 三灵根（30%）──
    ("三灵根", ["金","木","水"], 10, "common",
     "三系灵根，中人之资，修行路上需勤勉以补天赋之不足"),
    ("三灵根", ["火","土","金"], 10, "common",
     "三系灵根，中人之资，修行路上需勤勉以补天赋之不足"),
    ("三灵根", ["水","木","火"], 10, "common",
     "三系灵根，中人之资，修行路上需勤勉以补天赋之不足"),
    # ── 双灵根（18%）──
    ("双灵根", ["金","水"], 6, "uncommon",
     "金水双系，相辅相成，天赋不俗，宗门争抢的好苗子"),
    ("双灵根", ["木","火"], 6, "uncommon",
     "木火双系，生生不息，天赋不俗，宗门争抢的好苗子"),
    ("双灵根", ["土","金"], 6, "uncommon",
     "土金双系，根基扎实，天赋不俗，宗门争抢的好苗子"),
    # ── 天灵根（5%）──
    ("天灵根", ["金"], 1, "rare",
     "单一金灵根——万中无一！灵力如刀锋般锐利纯粹，修炼速度远超同辈"),
    ("天灵根", ["木"], 1, "rare",
     "单一木灵根——万中无一！灵力如春藤般生生不息，修炼速度远超同辈"),
    ("天灵根", ["水"], 1, "rare",
     "单一水灵根——万中无一！灵力如江河般绵延不绝，修炼速度远超同辈"),
    ("天灵根", ["火"], 1, "rare",
     "单一火灵根——万中无一！灵力如烈焰般炽烈纯粹，修炼速度远超同辈"),
    ("天灵根", ["土"], 1, "rare",
     "单一土灵根——万中无一！灵力如大地般厚重深沉，修炼速度远超同辈"),
    # ── 异灵根（5%）──
    ("异灵根", ["风"], 2, "rare",
     "风灵根——水之变异，来去无踪。风系灵力锋锐灵动，同阶无敌"),
    ("异灵根", ["雷"], 2, "rare",
     "雷灵根——火之变异，天威煌煌。雷系灵力霸道刚猛，万灵辟易"),
    ("异灵根", ["冰"], 1, "rare",
     "冰灵根——水之极变，封冻万物。冰系灵力冷冽纯粹，一念冰封千里"),
    # ── 特殊灵根（1.5%）──
    ("混沌灵根", ["混沌"], 1, "legendary",
     "混沌灵根——万古无一！不受五行束缚，可纳万法于一身，天道眷顾"),
    ("阴阳灵根", ["阴阳"], 0.5, "legendary",
     "阴阳灵根——逆天改命！阴阳交汇于一体，蕴含天地至理，亿万人中无一"),
    # ── 天漏之体（0.5%）──
    ("天漏之体", [], 0.5, "cursed",
     "天漏之体——经脉天生残缺，灵气入体即散，如竹篮打水，此生注定无法修仙"),
]

def main(character_id: int, character_name: str, infomation: str) -> dict:
    """
    灵根觉醒器 —— 按概率表随机抽取灵根。

    Dify Code Tool 入口函数，由 Agent 节点在合适的叙事时机调用。
    返回灵根结果供 Agent 融入叙事。
    """

    # 1. 防重复觉醒
    try:
        info = json.loads(infomation) if isinstance(infomation, str) else infomation
    except (json.JSONDecodeError, TypeError):
        info = {}

    existing_roots = (
        info.get("cultivation", {}).get("spiritual_roots", [])
    )
    if existing_roots and len(existing_roots) > 0:
        return {
            "already_awakened": True,
            "message": f"角色 {character_name} 灵根已觉醒，无需重复",
            "spiritual_roots": existing_roots
        }

    # 2. 按权重随机抽取
    weights = [r[2] for r in SPIRITUAL_ROOT_TABLE]
    chosen = random.choices(SPIRITUAL_ROOT_TABLE, weights=weights, k=1)[0]

    category = chosen[0]   # 伪灵根 / 三灵根 / 天灵根 / 异灵根 / 混沌灵根 / 天漏之体
    roots = chosen[1]       # ["金","水"] 或 ["混沌"] 或 []
    rarity = chosen[3]      # common / uncommon / rare / legendary / cursed
    seed = chosen[4]        # 叙事种子（给 Agent 的创作提示）

    # 3. 构建灵根描述
    if len(roots) == 0:
        root_desc = f"天漏之体——{seed}"
    elif len(roots) == 1:
        root_desc = f"单一{roots[0]}灵根（{category}）。{seed}。"
    else:
        elements = "、".join(roots)
        root_desc = f"{elements}（{category}）。{seed}。"

    return {
        "already_awakened": False,
        "character_name": character_name,
        "spiritual_roots": roots,
        "root_category": category,
        "root_rarity": rarity,
        "root_description": root_desc,
        "awakening_seed": seed
    }
```

---

## 三、稀有度分布

| 稀有度 | 标签 | 总概率 | 包含 |
|--------|------|--------|------|
| 普通 | common | 70% | 伪灵根 + 三灵根 |
| 稀有 | uncommon | 18% | 双灵根 |
| 珍稀 | rare | 10% | 天灵根 + 异灵根 |
| 传说 | legendary | 1.5% | 混沌灵根 + 阴阳灵根 |
| 诅咒 | cursed | 0.5% | 天漏之体 |

---

## 四、Agent 如何使用此工具

Agent 的 System Prompt（`05b-system-prompt-narrative.md`）已包含工具使用说明：

```
### awaken-spiritual-roots
- 用途：觉醒角色的灵根
- 调用时机：当玩家经历测灵石、灵池、被探查根骨等场景
- 约束：仅在角色尚未觉醒灵根时调用
- 调用后：工具返回灵根结果，你将结果自然融入叙事
```

**Agent 调用 → 工具返回 → Agent 融入叙事的完整流程**：

```
Agent 接收到玩家输入"我把手放在测灵石上"
  → Agent 判断：这是灵根测试场景，角色 spiritual_roots=[]
  → Agent 调用 awaken-spiritual-roots(character_id=1, character_name="云逸", infomation="{...}")
  → 工具返回: { spiritual_roots: ["金"], root_category: "天灵根", root_rarity: "rare", ... }
  → Agent 融入叙事: "你的手掌触及测灵石的瞬间——金光！璀璨的金光如利剑般从灵石内部迸发..."
  → Agent 输出 info_changes: { cultivation: { spiritual_roots: ["金"] } }
```

---

## 五、后端持久化

灵根结果通过 `info_changes` 传递给后端，由 `merge_infomation()` 自动合并到 `cultivation.spiritual_roots`。后端额外记录觉醒事件日志：

```python
def log_awakening(character_id: int, spiritual_roots: list, root_rarity: str):
    """记录灵根觉醒系统消息"""
    metadata = {
        "event_type": "spiritual_root_awakening",
        "roots": spiritual_roots,
        "rarity": root_rarity
    }
    with get_db() as conn:
        conn.execute(
            "INSERT INTO messages (character_id, role, content, metadata) "
            "VALUES (?, 'system', ?, ?)",
            (character_id, "【天道裁定】灵根觉醒", json.dumps(metadata))
        )
```

---

## 六、安全机制

| 机制 | 实现 |
|------|------|
| 防重复觉醒 | 工具内检查 spiritual_roots 是否已非空 |
| Agent 层约束 | System Prompt 明确"仅在 spiritual_roots=[] 时调用" |
| 日志可追溯 | 后端写入 system 消息记录觉醒事件 |
| 概率不可干预 | 纯代码随机，LLM 无法影响结果 |

---

## 七、扩展：未来工具模板

新增工具只需：

1. **注册 Dify Code Tool**：名称、描述、输入参数、Python 代码
2. **System Prompt 追加工具说明**：在"你的工具"段落加一条
3. **Agent 自主调用**：无需修改任何路由逻辑

| 工具 | 触发场景 | 优先级 |
|------|----------|--------|
| `breakthrough-judge` | 境界突破 | Phase 4 |
| `tribulation-calc` | 渡劫 | Phase 4 |
| `battle-resolver` | 战斗裁定 | Phase 5 |

---

*05c-tool-spiritual-roots.md v2.0。关联：[05-dify-workflows.md](./05-dify-workflows.md) | [05b-system-prompt-narrative.md](./05b-system-prompt-narrative.md)。*
