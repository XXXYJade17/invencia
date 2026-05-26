# 玄天界 —— 工具设计

> 版本：v2.0
> 日期：2026-05-25
> 变更：灵根觉醒工具移除。新增道韵评定工具。工具框架适配武道化。
> 调用方：Dify Chatflow Agent 节点（天道推演时自主调用）

---

## 一、工具总览

| 工具 | 触发场景 | Dify 类型 | Phase |
|------|----------|-----------|-------|
| `dao-rhyme-assess` | 道韵评定（感悟/突破/生死关） | Code Tool | Phase 1（MVP） |
| `breakthrough-judge` | 境界突破 | Code Tool | Phase 4 |
| `tribulation-calc` | 生死关/渡劫 | Code Tool | Phase 4 |
| `battle-resolver` | 战斗裁定 | Code Tool | Phase 5 |

---

## 二、dao-rhyme-assess（道韵评定器）

### 2.1 Dify 配置

| 配置项 | 值 |
|--------|-----|
| 名称 | `dao-rhyme-assess` |
| 类型 | Code Tool（Python） |
| 描述 | 评定角色的道韵层级变化。根据触发事件类型和当前道韵层级，判定是否晋升及晋升幅度，返回新评级和叙事引导。 |
| 输入参数 | |
| | `character_id` (number, required) — 角色 ID |
| | `character_name` (string, required) — 角色名 |
| | `current_rhyme` (string, required) — 当前道韵评级名（如"蒙昧""通明"等） |
| | `trigger_event` (string, required) — 触发事件类型：minor_epiphany / major_epiphany / breakthrough / life_death / destiny_turn |

### 2.2 工具代码

```python
import random

# ============================================================
# 道韵十二重
# ============================================================
DAO_RHYME_LEVELS = [
    "蒙昧", "启蒙", "初窥", "入境",
    "凝脉", "洗髓", "归真",
    "通明", "化物", "天人",
    "近道", "证道"
]

# ============================================================
# 各事件类型的晋升幅度表
# 格式: { 事件类型: { 概率权重: 晋升重数 } }
# ============================================================
PROMOTION_TABLE = {
    "minor_epiphany": {
        # 小感悟：65% 不变，30% 升1重，5% 升2重
        "weights": [65, 30, 5],
        "steps": [0, 1, 2]
    },
    "major_epiphany": {
        # 大感悟：20% 不变，50% 升1重，25% 升2重，5% 升3重
        "weights": [20, 50, 25, 5],
        "steps": [0, 1, 2, 3]
    },
    "breakthrough": {
        # 境界突破：50% 升1重，40% 升2重，10% 升3重
        "weights": [50, 40, 10],
        "steps": [1, 2, 3]
    },
    "life_death": {
        # 生死关头：15% 升1重，35% 升2重，30% 升3重，15% 升4重，5% 升5重
        "weights": [15, 35, 30, 15, 5],
        "steps": [1, 2, 3, 4, 5]
    },
    "destiny_turn": {
        # 命运转折：30% 升2重，40% 升3重，20% 升4重，10% 升5重
        "weights": [30, 40, 20, 10],
        "steps": [2, 3, 4, 5]
    }
}

# ============================================================
# 道韵叙事种子（晋升到每一重的典型叙事引导）
# ============================================================
RHYME_NARRATIVE_SEEDS = {
    "启蒙": "回看自己打出的那一拳，恍然发现与昨日似乎不同——力道不再四散。不是变强了，是力气不再和自己打架了。",
    "初窥": "战斗中忽然有了一个瞬间——看不清，但能'感受到'对方的招式走向。那不是眼睛看到的，是某种更深的东西在苏醒。",
    "入境": "坐在山崖边看着落日。体内的力量忽然像找到了河道的水——不再横冲直撞，开始有了自己的节奏和方向。",
    "凝脉": "每一丝元气都像在经络中沉淀了下来。同样的招式，今日打出去比昨日多了一种说不清的'分量'。不是更重，是更沉。",
    "洗髓": "一次全力出手之后，浑身汗如雨下——但汗水里带着一丝灰黑色的杂质。那不是身体的污垢，是道韵在逼出元力中的'杂质'。",
    "归真": "忽然觉得自己打出的拳变'简单'了。招式还是那些招式，但少了很多多余的东西——像一块矿石终于炼成了铁。不华丽，但纯粹。",
    "通明": "心念一动，拳已至。不是更快了——是心和拳之间的那个'等待'消失了。他第一次理解了什么叫'意在拳先'。",
    "化物": "一拳打出，拳头还没到，空气先被压出了肉眼可见的波纹。那不是元气外放——是拳头裹挟着'理'。对手感到的不是攻击，是整片天地在压过来。",
    "天人": "他站在那，什么都没做。但方圆百丈内的元气在向他流动——不是吞噬，是朝拜。同境武者在他面前，连呼吸都觉得困难。",
    "近道": "力量本身开始变得不像力量。像秩序、像法则、像天地运行的一个自然环节。一拳打出去，道韵先行，肉身在后。",
    "证道": "他的一拳和道本身已无区别。这一拳不是'蕴含着道'——这一拳'就是道'。同境？不，已没有同境这个概念了。"
}

def main(character_id: int, character_name: str, current_rhyme: str, trigger_event: str) -> dict:
    """
    道韵评定器 —— 根据触发事件判定道韵是否晋升。

    Dify Code Tool 入口函数，由 Agent 节点在合适的叙事时机调用。
    返回道韵评定结果供 Agent 融入叙事。
    """

    # 1. 获取当前层级索引
    if current_rhyme not in DAO_RHYME_LEVELS:
        return {
            "error": True,
            "message": f"未知道韵评级: {current_rhyme}"
        }

    current_idx = DAO_RHYME_LEVELS.index(current_rhyme)

    # 2. 已达最高级
    if current_idx >= len(DAO_RHYME_LEVELS) - 1:
        return {
            "promoted": False,
            "current_rhyme": "证道",
            "message": f"角色 {character_name} 已臻证道之境，道无止境但评级已至顶。",
            "narrative_hint": "道无止境，证道之后仍有路——但那是另一条路了，不在十二重之中。"
        }

    # 3. 获取对应事件的晋升表
    if trigger_event not in PROMOTION_TABLE:
        return {
            "error": True,
            "message": f"未知触发事件类型: {trigger_event}"
        }

    table = PROMOTION_TABLE[trigger_event]
    steps = random.choices(table["steps"], weights=table["weights"], k=1)[0]

    # 4. 计算新层级（不越界）
    new_idx = min(current_idx + steps, len(DAO_RHYME_LEVELS) - 1)
    new_rhyme = DAO_RHYME_LEVELS[new_idx]

    # 5. 构建结果
    promoted = new_idx > current_idx
    result = {
        "promoted": promoted,
        "character_name": character_name,
        "previous_rhyme": current_rhyme,
        "current_rhyme": new_rhyme,
        "rhyme_index": new_idx + 1,  # 1-based
        "steps_gained": steps,
        "trigger_event": trigger_event
    }

    if promoted:
        narrative_seed = RHYME_NARRATIVE_SEEDS.get(new_rhyme, "")
        result["narrative_hint"] = narrative_seed
        result["message"] = f"道韵晋升！{current_rhyme} → {new_rhyme}（{trigger_event}，晋升 {steps} 重）"
    else:
        result["narrative_hint"] = "虽有所感，但道韵尚未质变。内力中多了一丝说不清道不明的东西——像种子刚埋入土中。"
        result["message"] = f"道韵未升。{current_rhyme} 保持不变。（{trigger_event}）"

    return result
```

### 2.3 Agent 如何使用返回结果

工具返回后：

1. 如果 `promoted: true` → Agent 将 `narrative_hint` 融入当前叙事，同时更新 `info_changes.combat_rating` 为新评级。
2. 如果 `promoted: false` → Agent 用 `narrative_hint` 描述"感悟但未质变"的状态，不更新 `combat_rating`。

```
Agent 输出 info_changes:
{
  "combat_rating": "入境——正式踏入了道的门槛。不是在战斗中学会的，是在...（融入 narrative_hint）"
}
```

### 2.4 道韵不倒退原则

根据设计，道韵是"悟"的累积——不会因为一场败仗而倒退。特殊情况下（如心魔侵蚀、道心崩塌），Agent 可通过叙事暗示道韵动摇，但评级不做数字式的回退。

---

## 三、未来工具模板

新增工具遵循统一模式：

1. **注册 Dify Code Tool**：名称、描述、输入参数、Python 代码
2. **System Prompt 追加工具说明**：在 `03-prompts.md` §二 的"你的工具"段落加一条
3. **Agent 自主调用**：无需修改任何路由逻辑

### breakthrough-judge（境界突破，Phase 4）

```
输入：character_id, character_data, target_realm
逻辑：根据当前境界、道韵、肉身/元神状态判断突破成功率
输出：{ success: bool, result_desc: string, side_effects: string[] }
```

### tribulation-calc（生死关，Phase 4）

```
输入：character_id, character_data
逻辑：根据境界、道韵、因果计算生死关强度
输出：{ trial_level: int, nature: string, survival_hint: string }
```

---

*玄天界工具设计 v2.0。*
