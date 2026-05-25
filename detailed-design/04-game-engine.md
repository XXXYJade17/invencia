# 04 —— 游戏核心引擎详细设计

> 版本：v2.0
> 日期：2026-05-25
> 依赖：03-characters.md（角色数据 + infomation merge）、05-dify-workflows.md（Dify Workflow + Chatflow Agent）
>
> **v2.0 变更**：平台切至 Dify。API 调用适配 Dify Workflow/Chatflow API。工具调度由 Dify Agent 内部处理，后端无需感知。

---

## 一、核心游戏循环（Game Loop）

### 1.1 单次交互流程

```
玩家输入文本
  │
  ├─ 1. 加载上下文
  │     ├── 从 DB 读取角色当前 infomation
  │     └── 从 DB 读取最近 N 条对话历史（默认 20 条）
  │
  ├─ 2. 调用 Dify Chatflow（Agent 自主处理工具调用）
  │     └── 传入上下文 + System Prompt → Agent 叙事 → 工具调用（如灵根觉醒） → 返回完整结果
  │
  ├─ 3. 解析响应
  │     ├── 提取 narrative（叙事文本）
  │     ├── 提取 hooks（钩子列表，2-4 个）
  │     └── 提取 info_changes（infomation 增量更新）
  │
  ├─ 4. 更新状态
  │     ├── merge_infomation(current, info_changes)
  │     └── UPDATE characters SET infomation = ...
  │
  ├─ 5. 持久化消息
  │     ├── INSERT message (role=user, content=玩家输入)
  │     └── INSERT message (role=assistant, content=叙事文本, metadata=...)
  │
  └─ 6. 返回前端
        └── { narrative, hooks, info_changes, character }
```

### 1.2 核心实现

```python
CONTEXT_MESSAGE_LIMIT = 20

def process_player_action(character_id, user_id, content):
    """处理玩家的一次行动输入，返回 AI 叙事响应"""

    # 1. 加载角色数据
    character = get_character(character_id, user_id)
    if not character:
        raise ValueError("角色不存在")
    if character["is_dead"]:
        raise ValueError("角色已陨落")

    # 2. 加载对话历史
    history = load_recent_messages(character_id, 20)

    # 3. 读取 System Prompt
    system_prompt = load_prompt("narrative.txt")

    # 4. 调用 Dify Chatflow API
    try:
        result = call_dify_chatflow(
            character_name=character["name"],
            infomation=character["infomation"],
            history=history,
            player_input=content,
            system_prompt=system_prompt,
            conversation_id=character.get("dify_conversation_id", "")
        )
    except Exception as e:
        raise RuntimeError(f"天道暂时无法回应: {e}")

    narrative = result["narrative"]
    hooks = result["hooks"]
    info_changes = result["info_changes"]
    metadata = result["metadata"]
    conversation_id = result.get("conversation_id", "")

    if not narrative:
        raise RuntimeError("AI 未生成有效叙事")

    # 5. 合并 infomation
    try:
        new_info = merge_infomation(character["infomation"], info_changes)
    except Exception:
        new_info = character["infomation"]

    # 6. 持久化
    with get_db() as conn:
        conn.execute(
            "UPDATE characters SET infomation=?, dify_conversation_id=?, updated_at=datetime('now','localtime') WHERE id=?",
            (json.dumps(new_info, ensure_ascii=False), conversation_id, character_id))
        conn.execute(
            "INSERT INTO messages (character_id,role,content) VALUES (?,'user',?)",
            (character_id, content))
        conn.execute(
            "INSERT INTO messages (character_id,role,content,metadata) VALUES (?,'assistant',?,?)",
            (character_id, narrative, json.dumps(metadata) if metadata else None))

    # 7. 灵根觉醒事件日志
    if metadata.get("event_type") == "awakening":
        log_awakening(character_id, new_info["cultivation"]["spiritual_roots"],
                       metadata.get("root_rarity", "unknown"))

    return {"narrative":narrative, "hooks":hooks,
        "info_changes":info_changes, "character":{**character, "infomation":new_info}}
```

---

## 二、Dify API 调用封装

### 2.1 Chatflow API（天道推演）

```python
import httpx, json, os

DIFY_API_BASE = os.getenv("DIFY_API_BASE", "https://api.dify.ai")
DIFY_API_KEY = os.getenv("DIFY_API_KEY")

async def call_dify_chatflow(
    character_name: str,
    infomation: dict,
    history: list,
    player_input: str,
    system_prompt: str,
    conversation_id: str = ""
):
    """调用 Dify Chatflow API"""
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
        "user": f"char-{character_name}"
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(url, json=body, headers=headers)
        resp.raise_for_status()
        result = resp.json()

    answer = result.get("answer", "")
    conv_id = result.get("conversation_id", "")

    # 解析 Agent 输出（JSON 格式）
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

### 2.2 Workflow API（角色创建）

```python
DIFY_WF_API_KEY = os.getenv("DIFY_WF_API_KEY")

async def call_dify_workflow(char_name: str, char_gender: str, system_prompt: str):
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

    outputs = result.get("data", {}).get("outputs", {})
    if outputs.get("error"):
        raise RuntimeError(f"角色创建失败: {outputs['error']}")

    return json.loads(outputs["infomation"])
```

---

## 三、工具调度（Dify Agent 内部处理）

Dify Agent 原生 function calling 使后端无需关心工具调度：

```
后端                     Dify Chatflow 内部
─────                    ─────────────────
传参 + System Prompt  →  Agent 接收
                         Agent 推理：需要调用工具？
                         ├─ 是 → 调用 Tool → 获取结果 → 继续推理
                         └─ 否 → 直接输出
                      →  Agent 输出最终 JSON
                      ←  后端收到完整结果
```

后端只需：**传参 + 收结果 + 持久化**。工具调度逻辑完全由 Dify Agent 自主处理。

---

## 四、上下文组装策略

### 4.1 对话历史加载

```python
def load_recent_messages(character_id: int, limit: int = 20) -> list[dict]:
    """加载最近 N 条对话历史，按时间正序"""
    with get_db() as conn:
        rows = conn.execute(
            """SELECT role, content FROM (
                SELECT role, content, created_at
                FROM messages
                WHERE character_id = ? AND del_flag = 0
                ORDER BY id DESC
                LIMIT ?
            ) ORDER BY created_at ASC""",
            (character_id, limit)
        ).fetchall()
    return [dict(r) for r in rows]
```

### 4.2 上下文窗口管理

| 策略 | 值 | 说明 |
|------|-----|------|
| 历史消息上限 | 20 条 | 平衡 Token 消耗与连贯性 |
| infomation 全量传入 | 是 | 含 spiritual_roots，确保 Agent 理解角色现状 |
| conversation_id | Dify 维护 | 可选：Dify 侧自动管理对话历史 |
| System Prompt | 后端传入 | Git 版本控制，支持多世界 |

---

## 五、消息历史加载

### 5.1 分页加载

```python
def load_messages(character_id: int, before_id: int | None = None,
                  limit: int = 50) -> dict:
    """分页加载对话历史，返回消息列表 + 是否有更多"""
    with get_db() as conn:
        if before_id:
            rows = conn.execute(
                """SELECT id, role, content, metadata, created_at
                FROM messages
                WHERE character_id = ? AND del_flag = 0 AND id < ?
                ORDER BY id DESC
                LIMIT ?""",
                (character_id, before_id, limit + 1)
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT id, role, content, metadata, created_at
                FROM messages
                WHERE character_id = ? AND del_flag = 0
                ORDER BY id DESC
                LIMIT ?""",
                (character_id, limit + 1)
            ).fetchall()

    has_more = len(rows) > limit
    if has_more:
        rows = rows[:limit]

    messages = [dict(r) for r in rows]
    messages.reverse()

    return {"messages": messages, "has_more": has_more}
```

---

## 六、事件日志

```python
def log_awakening(character_id: int, spiritual_roots: list, root_rarity: str):
    """记录灵根觉醒事件"""
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

## 七、错误处理与降级策略

| 场景 | 后端处理 | 前端表现 |
|------|----------|----------|
| Dify API 超时（60s） | 重试 2 次后抛出 RuntimeError | "天道暂时无法回应" + 重试按钮 |
| Agent 输出非 JSON | 降级：将原始文本作为 narrative，不更新 infomation | 叙事正常显示，角色面板不更新 |
| info_changes 解析失败 | merge_infomation 忽略 | 该字段保持原值 |
| 工具调用异常（Dify 内部） | Agent 自行处理或返回错误 | 叙事中体现异常或跳过 |
| 数据库写入失败 | 事务回滚，抛出异常 | 错误提示，输入不丢失（前端缓存） |

---

*04-game-engine.md v2.0。下一步：[05-dify-workflows.md](./05-dify-workflows.md)。*
