# 智能体架构决策（修订版）：两工作流 + 务实选型

> 日期：2026-05-23
> 修订：v2.0 —— 重新评估 Dify 对两工作流场景的适配度

---

## 一、重新审视：Invencia 的智能体本质

用户指出了我之前分析的一个盲点：**Invencia 的智能体不是"一个"需要自由发挥的 AI，而是两个边界清晰的固定工作流**。

| 工作流 | 输入 | 输出 | 确定性 |
|---|---|---|---|
| **角色创建** | name + gender | infomation（10 字段 全叙事） | 高——Prompt 固定，输出结构固定 |
| **天道推演** | 玩家输入 + 历史 + infomation | narrative + hook + info_changes | 高——格式固定，内容开放 |

这两个工作流的共同特征：
- **输入输出格式高度结构化**（JSON in / JSON out）
- **Prompt 相对稳定**（世界观不变、叙事规则不变）
- **不需要 LLM 动态决策"下一步做什么"**（不需要 Agent 的 tool-use 循环）

这就使得 **工作流平台（Dify）成为一个合理的选择**，而不是我之前说的"过度设计"。

---

## 二、Dify 方案：实际映射

### 2.1 工作流 1：角色创建

```
┌─────────────────────────────────────────────────┐
│              Dify Workflow: 角色创建              │
│                                                 │
│  [Start] ← API Trigger (POST /characters)        │
│    │ name, gender                                │
│    ↓                                            │
│  [变量赋值]                                       │
│    组装 Character Creation Prompt                │
│    ↓                                            │
│  [LLM] ← DeepSeek / 千问                         │
│    System: "你是天道，正在为一个凡人编织命运..."       │
│    User: "性别{gender}，名{name}..."              │
│    ↓                                            │
│  [代码] ← JSON 解析 + 字段校验                    │
│    提取 10 个 infomation 子字段                   │
│    确保每个字段非空且长度合理                       │
│    ↓                                            │
│  [HTTP 请求] ← 回调 FastAPI                       │
│    POST /internal/character/{id}/infomation       │
│    写入数据库                                     │
│    ↓                                            │
│  [End] → 返回 infomation JSON                    │
└─────────────────────────────────────────────────┘
```

### 2.2 工作流 2：天道推演

```
┌─────────────────────────────────────────────────┐
│              Dify Workflow: 天道推演              │
│                                                 │
│  [Start] ← API Trigger (POST /game/:id/act)      │
│    │ character_id, user_input                    │
│    ↓                                            │
│  [HTTP 请求] ← 调 FastAPI 取上下文                │
│    GET /internal/character/{id}/context           │
│    返回: { infomation, recent_messages[] }       │
│    ↓                                            │
│  [变量赋值]                                       │
│    组装完整 System Prompt:                        │
│    世界 Prompt + infomation + 叙事规则             │
│    ↓                                            │
│  [LLM] ← DeepSeek / 千问                         │
│    Messages: [system, ...history, user_input]    │
│    ↓                                            │
│  [代码] ← JSON 解析                              │
│    提取 narrative, hook, info_changes             │
│    校验字段完整性                                 │
│    ↓                                            │
│  [HTTP 请求] ← 回调 FastAPI 持久化                 │
│    POST /internal/game/persist                    │
│    { narrative, hook, info_changes }             │
│    FastAPI 负责:                                  │
│      - t_message INSERT × 2                      │
│      - t_character.infomation merge               │
│    ↓                                            │
│  [End] → 返回 { narrative, hook }                │
└─────────────────────────────────────────────────┘
```

### 2.3 JSON 解析插件

两个工作流共用同一个解析逻辑，封装为 Dify 代码插件：

```python
# Dify Code Plugin: json_validator
def main(response_text: str, schema_type: str) -> dict:
    """解析 LLM 输出的 JSON，按 schema_type 校验"""
    
    schemas = {
        "character_creation": {
            "required": ["realm", "power", "origin", "obsession", "location",
                        "dao_heart", "causality", "relationships", "inventory", "summary"],
            "max_length": 2000
        },
        "game_act": {
            "required": ["narrative", "hook"],
            "optional": ["info_changes"],
            "max_narrative": 2000,
            "max_hook": 300
        }
    }
    
    schema = schemas[schema_type]
    data = json.loads(extract_json(response_text))
    
    # 校验必填字段
    for field in schema["required"]:
        if field not in data or not data[field]:
            raise ValueError(f"Missing required field: {field}")
    
    return data
```

---

## 三、架构：FastAPI + Dify 混合

```
┌──────────────────────────────────────────┐
│              前端 (HTML/CSS/JS)            │
└──────────────┬───────────────────────────┘
               │ HTTP
┌──────────────▼───────────────────────────┐
│            FastAPI（业务层）               │
│                                          │
│  /api/auth/*      注册/登录/JWT           │
│  /api/characters   角色 CRUD              │
│  /api/game/:id/act 游戏入口 → 调 Dify      │
│                                          │
│  /internal/character/{id}/context         │
│    提供上下文数据（infomation + 消息）       │
│                                          │
│  /internal/game/persist                   │
│    持久化叙事 + merge infomation           │
└──────────────┬───────────────────────────┘
               │ HTTP（内网）
┌──────────────▼───────────────────────────┐
│           Dify（AI 层）                    │
│                                          │
│  Workflow "角色创建"                       │
│    Prompt 组装 → LLM → JSON 解析           │
│                                          │
│  Workflow "天道推演"                       │
│    取上下文 → Prompt → LLM → JSON 解析      │
│                                          │
│  共享插件：json_validator                  │
└──────────────┬───────────────────────────┘
               │ API
┌──────────────▼───────────────────────────┐
│       DeepSeek / 通义千问                 │
└──────────────────────────────────────────┘
```

**职责划分**：

| 层 | 职责 | 技术 |
|---|---|---|
| FastAPI | 用户系统、会话管理、数据库 CRUD、infomation merge | Python |
| Dify | Prompt 管理、LLM 编排、输出解析、重试 | 可视化工作流 + 代码插件 |
| LLM | 叙事生成、战斗判定、infomation 内容创作 | DeepSeek / 千问 |

---

## 四、务实对比：Dify vs 原生

### 4.1 Dify 的**真实**优势

| 优势 | 说明 |
|---|---|
| **Prompt 版本管理** | 每次调 Prompt 都有记录，A/B 对比有依据。Prompt 迭代是 Invencia 的核心工作，这点很重要 |
| **LLM 可观测性** | 每次调用的 Token 消耗、延迟、成本自动记录，不需要自己打日志 |
| **可视化调试** | 工作流跑一半出问题，能看到每个节点的输入输出，定位比 grep 日志快 |
| **热更新 Prompt** | 改 Prompt 不需要重新部署 FastAPI，Dify 里改了立即生效 |
| **非开发协作** | 如果后续有文案/策划同学参与 Prompt 调优，Dify 的界面比代码友好 |

### 4.2 Dify 的**真实**代价

| 代价 | 说明 |
|---|---|
| **多一次网络跳转** | FastAPI → Dify → LLM，比直连多 ~50-100ms 延迟 |
| **额外部署** | 需要维护一个 Dify 实例（Docker Compose 一键部署，但毕竟多一个服务） |
| **内部 API 维护** | 需要设计 `/internal/*` 接口供 Dify 回调，增加前后端协议约定 |
| **代码分散** | 业务逻辑分在 FastAPI 和 Dify 两处，排查问题要两边看 |
| **Dify 版本锁定** | Dify 更新频繁，升级可能影响工作流兼容性 |

### 4.3 结论：不是哪个更好，是什么时候用哪个

```
Invencia 的当前阶段：

┌─────────────────────────────────────────────┐
│  只有一个开发者（你）                           │
│  两个固定工作流                                │
│  Prompt 需要频繁迭代（找手感）                   │
│  需要看到每次 AI 调用的 Token 消耗和延迟          │
└─────────────────────────────────────────────┘
         │
         ▼
    Dify 比原生 API 多出来的运维成本 < 省下的调试时间
         │
         ▼
    Dify 是当前阶段更务实的选择
```

但如果未来：
- 团队全是开发者 → 原生 API 更直接
- Prompt 稳定不再频繁改 → Dify 的多一层跳转变成纯负担
- 需要极致性能 → 原生 API 省 50ms

**那时迁移到原生 API 的成本很低**——就是把 Dify 工作流里的逻辑搬到 FastAPI 一个函数里，工作量不超过半天。

---

## 五、最终推荐

| 决策 | 结论 |
|---|---|
| **当前阶段** | **FastAPI + Dify 混合架构**，两工作流跑在 Dify，业务跑在 FastAPI |
| **Dify 部署** | Docker Compose 自部署（社区版免费） |
| **迁移策略** | Dify 工作流逻辑保持简洁，随时可无损迁移到原生 API |
| **JSON 解析** | Dify 代码插件，两个工作流共享 |

### 实施路径

```
1. 搭 FastAPI 骨架（auth + character CRUD + /internal/* 接口）
2. 部署 Dify 实例
3. 在 Dify 中创建两个工作流
4. 编写 json_validator 代码插件
5. FastAPI /game/act 改为调 Dify API
6. 观察 Token 消耗和延迟，迭代 Prompt
```

---

*修订完成。核心转变：从"Dify 过度设计"到"Dify 在 Prompt 迭代阶段有真实价值"*。
