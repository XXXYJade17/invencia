# 05 —— Dify 工作流与智能体配置

> 版本：v4.2
> 日期：2026-05-25
> **v4.2 变更**：适配武道化。道韵评定工作流移除。
**v4.1 变更**：Prompt 和工具引用更新至 xuantian-realm/ 子目录。
> **v4.0 变更**：平台从 Coze 切换至 Dify。角色创建使用 Workflow，天道推演使用 Chatflow + Agent 节点（原生 function calling）。工具（道韵评定等）注册为 Dify Tool，Agent 自主判定调用时机。

---

## 一、平台选择：为什么是 Dify

| | Coze 工作流 | Dify Chatflow + Agent |
|---|---|---|
| LLM 自主调用工具 | ❌ 不支持，需手动模拟 | ✅ Agent 节点原生支持 |
| 工具注册 | 需两次 LLM 调用模拟 | 直接注册为 Tool，Agent 判定时机 |
| 开源自部署 | ❌ SaaS only | ✅ Docker 自部署 |
| API 调用 | 工作流 API | Chatflow API + Workflow API |
| 节点复杂度（天道推演） | 8 节点含分支 | 3 节点 |

---

## 二、Dify 资源规划

| 资源        | 类型        | 名称                       | 用途        |
| --------- | --------- | ------------------------ | --------- |
| Workflow  | Workflow  | `char-creation`          | 角色创建      |
| Chatflow  | Chatflow  | `tiandao-narrative`      | 天道推演      |
| Tool      | Code Tool | `dao-rhyme-assess` | 道韵评定器     |
| Tool      | Code Tool | `breakthrough-judge`     | 突破判定器（未来） |
| Tool      | Code Tool | `tribulation-calc`       | 天劫强度器（未来） |
| Knowledge | 知识库       | `xuantian-world`         | 玄天界世界观文档  |

---

## 三、Prompt 管理策略

Prompt 文本存放在后端代码仓库，每次调用 Dify 时作为输入变量传入。

```
backend/prompts/
├── char_create.txt         角色创建 System Prompt
├── narrative.txt            天道推演 System Prompt（Agent 用）
└── awakening.txt            觉醒叙事补充 Prompt（可选）
```

运行时后端读取 prompt 文件 → 作为 `inputs.system_prompt` 传给 Dify。

---

## 四、Workflow 一：角色创建

### 4.1 节点拓扑（Dify Workflow）

```
[开始]
  ↓
[代码: 上下文组装 + 出身抽签]
  输入: char_name, char_gender, system_prompt（后端传入）
  逻辑: 随机抽取出身 → 组装 User Prompt 文本
  输出: prompt_context (str), system_prompt (str 透传)
  ↓
[LLM: 角色画像生成]
  System Prompt: {{系统变量.system_prompt}}
  User Prompt: {{代码节点.prompt_context}}
  Temperature: 1.0
  输出: infomation_reasoning (str → LLM 原始输出)
  ↓
[代码: JSON 校验]
  输入: infomation_reasoning
  逻辑: 清理代码块标记 → JSON 解析 → 字段完整性校验 → 添加 combat_rating 字段存在
  输出: infomation (JSON str) | error (str)
  ↓
[结束]
```

**3 个节点**：代码 → LLM → 代码。

### 4.2 代码节点 A：上下文组装 + 出身抽签

```python
import random

ORIGIN_POOL = [
    ("山野散修", "无门无派，粗犷自由"),
    ("宗门弟子", "小宗门或大宗门外门"),
    ("修仙世家", "家族传承，荣辱与共"),
    ("凡人奇遇", "平淡中暗藏伏笔"),
    ("天外来客", "不属于此界的异乡人"),
]

def main(char_name: str, char_gender: str, system_prompt: str):
    origin_type, origin_seed = random.choice(ORIGIN_POOL)

    ctx = (
        f"角色名：{char_name}\n"
        f"性别：{char_gender}\n"
        f"出身：{origin_type}（{origin_seed}）\n"
        "请根据以上信息，生成完整角色画像 JSON。"
    )

    return {
        "prompt_context": ctx,
        "system_prompt": system_prompt,
        "origin_type": origin_type,
        "origin_seed": origin_seed
    }
```

### 4.3 LLM 节点

| 配置项 | 值 |
|--------|-----|
| 模型 | 国产大模型（DeepSeek / Qwen） |
| System Prompt | `{{#代码节点.system_prompt#}}` |
| User Prompt | `{{#代码节点.prompt_context#}}` |
| Temperature | 1.0 |
| 最大 Token | 4096 |

### 4.4 代码节点 B：JSON 校验

```python
import json

REQUIRED = [
    "basic_info", "cultivation", "physique", "mind_spirit",
    "inventory", "techniques", "relationships", "causality", "location"
]

def main(llm_output: str):
    t = llm_output.strip()
    # 清理代码块标记
    if t.startswith("```"):
        lines = t.split("\n")
        t = "\n".join(lines[1:])
    if t.endswith("```"):
        t = t[:-3]
    t = t.strip()

    try:
        data = json.loads(t)
    except json.JSONDecodeError as e:
        return {"error": f"JSON 解析失败: {e}"}

    # 顶层字段校验
    missing = [f for f in REQUIRED if f not in data]
    if missing:
        return {"error": f"缺少顶层字段: {missing}"}

    # 数组数量校验
    if not isinstance(data.get("inventory"), list) or len(data["inventory"]) < 2:
        return {"error": "inventory 至少需要 2 件物品"}
    if not isinstance(data.get("relationships"), list) or len(data["relationships"]) < 1:
        return {"error": "relationships 至少需要 1 人"}

    # 确保 combat_rating 为"蒙昧"（凡人模板）
    if "cultivation" in data:
        data["combat_rating"] = []

    return {"infomation": json.dumps(data, ensure_ascii=False)}
```

---

## 五、Chatflow 二：天道推演（Agent + 工具）

### 5.1 节点拓扑（Dify Chatflow）

```
[开始]
  ↓
[Agent: 天道]
  System Prompt: {{系统变量.system_prompt}}
  Tools:
    ├── dao-rhyme-assess  ← 道韵评定器
    ├── (breakthrough-judge)    ← 未来
    └── (tribulation-calc)      ← 未来
  输入变量:
    - character_name
    - infomation (JSON str)
    - history (JSON str)
    - system_prompt
  模型: 国产大模型, temperature=0.8
  ↓
[代码: 输出格式化]
  输入: Agent 最终输出文本
  逻辑: 提取 JSON → 校验 narrative/hooks/info_changes
  输出: formatted_output (JSON str)
  ↓
[结束]
```

**3 个节点**：开始 → Agent → 代码格式化 → 结束。

Agent 节点是 Dify Chatflow 的核心——它自动处理工具调用循环：
1. 接收用户输入 + System Prompt
2. LLM 判断是否需要调用工具 → 如需则调用 → 获取结果 → 继续推理
3. 最终输出完整叙事

### 5.2 Agent System Prompt 要点

详见 `xuantian-realm/03-prompts.md`。核心要点：

- 单一 System Prompt，描述天道角色、叙事规则、输出格式
- 明确告知 Agent 拥有 `dao-rhyme-assess` 工具：
  > 你拥有以下工具可用：
  > - `dao-rhyme-assess`：道韵评定。当玩家经历测道韵评定、进入灵池、被探查根骨等场景时调用。仅在角色尚未觉醒道韵评定时调用。

### 5.3 工具注册（Dify Tool 配置）

在 Dify 中注册 `dao-rhyme-assess` 为 **Code Tool**：

| 配置项 | 值 |
|--------|-----|
| 工具名称 | dao-rhyme-assess |
| 类型 | Code Tool (Python) |
| 描述 | 觉醒角色的道韵评定。按概率表随机抽取道韵评定类型，返回道韵评定元素列表、类别、稀有度和叙事种子。仅在角色尚未觉醒道韵评定时调用。 |
| 输入参数 | `character_id` (number, required) — 角色 ID |
| 输出格式 | JSON |

工具实现代码见 `xuantian-realm/04-tools.md`。

### 5.4 代码节点：输出格式化

```python
import json

def main(agent_output: str):
    t = agent_output.strip()
    # 清理代码块
    if t.startswith("```json"): t = t[7:]
    elif t.startswith("```"): t = t[3:]
    if t.endswith("```"): t = t[:-3]
    t = t.strip()

    try:
        data = json.loads(t)
    except json.JSONDecodeError as e:
        return {"error": f"JSON 解析失败: {e}", "raw": t}

    if not data.get("narrative"):
        return {"error": "缺少 narrative 字段", "raw": t}

    if not isinstance(data.get("hooks"), list):
        data["hooks"] = []
    if not isinstance(data.get("info_changes"), dict):
        data["info_changes"] = {}
    if "metadata" not in data:
        data["metadata"] = {"event_type": "normal"}

    return {"formatted_output": json.dumps(data, ensure_ascii=False)}
```

---

## 六、后端 API 调用封装

### 6.1 Dify 配置

```python
# backend/config.py
import os

DIFY_API_BASE = os.getenv("DIFY_API_BASE", "https://api.dify.ai")  # 或自部署地址
DIFY_API_KEY = os.getenv("DIFY_API_KEY")
DIFY_WF_API_KEY = os.getenv("DIFY_WF_API_KEY")  # Workflow 可用不同 Key

# Dify 应用 ID
DIFY_APP_CHAR_CREATE = os.getenv("DIFY_APP_CHAR_CREATE")  # Workflow
DIFY_APP_NARRATIVE = os.getenv("DIFY_APP_NARRATIVE")      # Chatflow
```

### 6.2 Workflow API 调用（角色创建）

```python
import httpx

async def call_workflow(char_name: str, char_gender: str, system_prompt: str):
    """调用 Dify Workflow API 进行角色创建"""
    url = f"{DIFY_API_BASE}/v1/workflows/run"
    headers = {
        "Authorization": f"Bearer {DIFY_WF_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "inputs": {
            "char_name": char_name,
            "char_gender": char_gender,
            "system_prompt": system_prompt
        },
        "response_mode": "blocking",
        "user": "system"
    }

    async with httpx.AsyncClient(timeout=45) as client:
        resp = await client.post(url, json=body, headers=headers)
        resp.raise_for_status()
        result = resp.json()

    # Dify Workflow 返回: { data: { outputs: { infomation: "..." } } }
    outputs = result.get("data", {}).get("outputs", {})
    if outputs.get("error"):
        raise RuntimeError(f"角色创建失败: {outputs['error']}")

    return json.loads(outputs["infomation"])
```

### 6.3 Chatflow API 调用（天道推演）

```python
import httpx, json

async def call_chatflow(
    character_name: str,
    infomation: dict,
    history: list,
    player_input: str,
    system_prompt: str,
    conversation_id: str = ""
):
    """调用 Dify Chatflow API 进行天道推演"""
    url = f"{DIFY_API_BASE}/v1/chat-messages"
    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}",
        "Content-Type": "application/json"
    }

    # 构建上下文文本
    info_text = json.dumps(infomation, ensure_ascii=False, indent=2)
    hist_text = ""
    for m in history[-20:]:
        role_label = "玩家" if m.get("role") == "user" else "天道"
        hist_text += f"{role_label}：{m.get('content', '')}\n"

    query = (
        f"--- 角色信息 ---\n{info_text}\n\n"
        f"--- 对话历史 ---\n{hist_text}\n\n"
        f"--- 玩家输入 ---\n{player_input}"
    )

    body = {
        "inputs": {
            "character_name": character_name,
            "system_prompt": system_prompt
        },
        "query": query,
        "response_mode": "blocking",
        "conversation_id": conversation_id,
        "user": f"character-{character_name}"
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(url, json=body, headers=headers)
        resp.raise_for_status()
        result = resp.json()

    # Dify Chatflow 返回: { answer: "...", conversation_id: "..." }
    answer = result.get("answer", "")
    conv_id = result.get("conversation_id", "")

    # 解析 Agent 输出（由代码节点格式化的 JSON）
    try:
        data = json.loads(answer)
    except json.JSONDecodeError:
        data = {"narrative": answer, "hooks": [], "info_changes": {}}

    return {
        "narrative": data.get("narrative", answer),
        "hooks": data.get("hooks", []),
        "info_changes": data.get("info_changes", {}),
        "metadata": data.get("metadata", {}),
        "conversation_id": conv_id
    }
```

### 6.4 会话管理

Dify Chatflow 原生支持 `conversation_id`：
- 首次调用时不传，Dify 返回新的 `conversation_id`
- 后续调用传入该 ID，Dify 自动维护对话历史
- 可选：将 `conversation_id` 存入 characters 表，持续对话

```python
# conversation_id 持久化
def save_conversation_id(character_id: int, conversation_id: str):
    with get_db() as conn:
        conn.execute(
            "UPDATE characters SET dify_conversation_id=?, updated_at=datetime('now','localtime') WHERE id=?",
            (conversation_id, character_id)
        )
```

> 注：需在 characters 表增加 `dify_conversation_id TEXT` 字段。

---

## 七、与 Coze 版的关键差异

| | Coze 版（v3.0） | Dify 版（v4.0） |
|---|---|---|
| 角色创建节点数 | 7 | 3 |
| 天道推演节点数 | 8（含手动分支） | 3（Agent 自动路由） |
| 工具调用方式 | 代码节点手动路由 | Agent 原生 function calling |
| 道韵评定并发 | 两次 LLM 调用 | Agent 内部循环，一次响应 |
| 会话管理 | 后端手动传 history | Dify conversation_id 自动维护 |
| 自部署 | ❌ | ✅ Docker |

---

*05-dify-workflows.md v4.0。关联：[05a](./xuantian-realm/03-prompts.md) | [05b](./xuantian-realm/03-prompts.md) | [05c](./xuantian-realm/04-tools.md)。*
