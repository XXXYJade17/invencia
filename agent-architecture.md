# 智能体架构决策：工作流 vs 对话流 vs 混合方案

> 日期：2026-05-23
> 背景：Invencia 需要 AI 驱动叙事 RPG，需确定智能体的实现范式和技术选型。

---

## 一、问题拆解

两个独立但相关的决策：

| 决策 | 问题 |
|---|---|
| **范式选择** | 智能体用"工作流"还是"对话流"实现？ |
| **平台选择** | 用 Coze / Dify / 原生 API？ |

---

## 二、工作流 vs 对话流：本质区别

### 2.1 工作流模式

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ 触发器   │ → │ LLM 节点 │ → │ 条件分支 │ → │ 代码节点 │ → ...
└─────────┘    └─────────┘    └─────────┘    └─────────┘
```

**特征**：预定义 DAG（有向无环图），节点串联，条件分支显式声明。每一步做什么由开发者预先编排。

**擅长**：
- 结构化业务流程（客服分流 → 意图识别 → 知识库检索 → 回复生成）
- 可预测、可审计、可复现
- 多人协作的复杂流水线

**对 Invencia 不适用**：
- 叙事 RPG 的精彩之处恰恰在于 **不可预测**——玩家输入"我假装投降，等首领转身时一刀捅进他后心"，AI 需要即时判断这属于战斗/社交/诡计，然后生成符合世界逻辑的叙事。这不是预定义分支能覆盖的。
- 境界突破、遭遇事件、NPC 反应——全部是 LLM 根据上下文**即时决定**的，不是流程图能画的。

### 2.2 对话流模式

```
┌──────────────┐
│ System Prompt │  ← 世界观 + 角色状态 + 叙事规则（一次性注入）
├──────────────┤
│ 历史消息 N 条  │  ← 上下文窗口
├──────────────┤
│ 玩家最新输入   │
└──────┬───────┘
       ↓
   LLM（一次调用）
       ↓
┌──────┴───────┐
│ narrative     │  ← 叙事正文
│ hook          │  ← 开放式钩子
│ info_changes  │  ← infomation 增量
└──────────────┘
```

**特征**：LLM 自身就是"引擎"。所有决策（叙事走向、战斗结果、境界突破、NPC 反应）均由 LLM 在单次调用中完成。

**擅长**：
- 创意写作、开放式叙事
- 需要 LLM 发挥"判断力"而非仅做"选择"的场景

**这正是 Invencia 的核心模式**。整个游戏循环本质上就是：组装 Prompt → 调 LLM → 解析结果 → 存库，一轮完成。

### 2.3 实际需求：对话流为主 + 轻量结构化外壳

纯粹的对话流有个问题：LLM 输出不可控。Invencia 需要的其实是：

```
对话流（叙事引擎）
    +
轻量结构化外壳（解析 / 校验 / Merge / 重试 / 降级）
```

即：**内核是对话流，外壳是结构化的**。

| 层 | 职责 | 范式 |
|---|---|---|
| 内核 | 叙事生成、战斗判定、境界突破、NPC 对话 | **对话流**（LLM 自由发挥） |
| 外壳 | Prompt 组装、JSON 解析、infomation merge、重试、降级 | **结构化代码**（FastAPI 路由内的业务逻辑） |

---

## 三、平台对比：Coze / Dify / 原生 API

### 3.1 Coze（扣子）

| 维度 | 评价 |
|---|---|
| 定位 |  chatbot 搭建平台（字节跳动） |
| 优势 | 可视化编排、插件市场、多端发布（飞书/微信/Web） |
| 劣势 | **封闭生态**，核心逻辑跑在字节云端；不适合创意写作类长文本；Prompt 控制精度不够 |
| 适合场景 | 客服机器人、知识问答、企业助手 |

**对 Invencia 的判断：❌ 不适用**
- Coze 的对话流是"意图识别 → 填槽 → 调用插件 → 生成回复"，这与 RPG 的"自由叙事 → 钩子 → infomation 更新"结构完全不同。
- 无法精细控制 JSON 输出格式（info_changes 协议）。
- 平台锁定风险：你的核心 IP（Prompt 设计、世界观、infomation 协议）绑在字节平台上。

### 3.2 Dify

| 维度 | 评价 |
|---|---|
| 定位 | 开源 LLM 应用开发平台 |
| 优势 | 自部署、可视化 Prompt 编排、知识库、工作流 + 对话流双模式 |
| 劣势 | 抽象层增加了复杂度；对话流模式下对长文本创意写作的控制力不如原生 API；Python/TypeScript 插件仍有限制 |
| 适合场景 | 企业内部 AI 应用、RAG 问答、简单的对话 Agent |

**对 Invencia 的判断：⚠️ 可选但非最优**
- Dify 的对话流模式可以做叙事，但中间多加了一层抽象（Dify 的对话管理、变量系统），不如直接调 API 灵活。
- 如果未来需要**非技术人员**参与 Prompt 调优，Dify 的可视化界面有优势。
- 但 Invencia 目前是纯开发团队，直接写 Prompt 字符串在代码里反而更快。

### 3.3 原生 API（DeepSeek SDK / OpenAI SDK）

| 维度 | 评价 |
|---|---|
| 定位 | 直接调用 LLM API |
| 优势 | **最大控制力**：Prompt 精确到字符、JSON 输出格式强制约束、重试策略自定义、成本完全可控 |
| 劣势 | 所有编排逻辑需自行实现（但 Invencia 的编排逻辑本身就不复杂） |
| 适合场景 | 需要精细控制的创意写作、游戏 AI、复杂 Agent |

**对 Invencia 的判断：✅ 推荐**
- Invencia 的核心循环极其简单：组装 Prompt → 调 LLM → 解析 JSON → Merge infomation。这用原生 API 只需要一个 50 行的函数。
- FastAPI 本身就是 Python，OpenAI SDK 兼容 DeepSeek 和千问（都支持 OpenAI 兼容接口）。
- 零平台锁定：换模型只需改 `base_url` 和 `api_key`。

### 3.4 对比总结

| 维度 | Coze | Dify | 原生 API |
|---|---|---|---|
| Prompt 控制精度 | 低 | 中 | **高** |
| JSON 输出约束 | 弱 | 中 | **强**（response_format） |
| 自部署 | ❌ | ✅ | ✅ |
| 多模型切换 | 受限 | 中 | **自由** |
| 学习成本 | 低 | 中 | 低（OpenAI SDK 三行代码） |
| 适合叙事 RPG | ❌ | ⚠️ | **✅** |
| 长期成本 | 平台费 + Token | 服务器 + Token | **仅 Token** |

---

## 四、推荐方案：原生 API + 轻量 Agent 层

### 4.1 架构

```
┌──────────────────────────────────────────────┐
│                  FastAPI 后端                  │
│                                              │
│  POST /api/game/:id/act                      │
│    │                                         │
│    ├── 1. 鉴权 & 参数校验                      │
│    ├── 2. 取最近 N 条消息（t_message）          │
│    ├── 3. 取角色 infomation（t_character）      │
│    ├── 4. 组装 System Prompt（world Prompt）    │
│    ├── 5. 调用 LLM（OpenAI 兼容 SDK）           │
│    ├── 6. 解析 JSON（narrative/hook/changes）   │
│    ├── 7. Merge infomation 增量                │
│    ├── 8. 写入 t_message（user + assistant）    │
│    └── 9. 返回 { narrative, hook, info }       │
│                                              │
│  AI 接入层（service/ai_client.py）             │
│    ├── chat(messages) → response              │
│    ├── retry（最多 2 次）                      │
│    ├── fallback（主模型失败 → 备用模型）        │
│    └── 模型配置（DeepSeek / 千问 base_url）     │
└──────────────────────────────────────────────┘
```

### 4.2 为什么不用 LangChain / LlamaIndex

Invencia 的核心流程太简单了，不需要 LangChain 的抽象层：

- 不需要 Chain（链式调用）：每次只是一次 LLM 调用
- 不需要 Agent（工具调用）：叙事不需要 function calling
- 不需要 RAG（检索增强）：上下文就是 infomation + 历史消息
- 不需要 Memory（记忆管理）：SQLite 直接存，精确控制取 N 条

引入 LangChain 只会增加依赖和调试难度，收益为零。

### 4.3 唯二需要的依赖

```txt
openai>=1.0.0      # DeepSeek / 千问 都兼容 OpenAI SDK
fastapi>=0.100.0   # 后端框架
```

DeepSeek 和千问都支持 OpenAI 兼容接口：

```python
from openai import OpenAI

# DeepSeek
client = OpenAI(api_key="sk-xxx", base_url="https://api.deepseek.com")

# 千问
client = OpenAI(api_key="sk-xxx", base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")

# 调用方式完全一致
response = client.chat.completions.create(
    model="deepseek-chat",  # 或 "qwen-plus"
    messages=[...],
    response_format={"type": "json_object"},  # 强制 JSON 输出
    temperature=0.8,  # 叙事需要一定随机性
)
```

### 4.4 核心代码量预估

| 模块 | 预估代码量 |
|---|---|
| AI 客户端封装（chat + retry + fallback） | ~80 行 |
| Prompt 组装（世界 Prompt + infomation + 历史） | ~60 行 |
| 叙事响应解析（JSON parse + 校验） | ~40 行 |
| infomation 增量 merge | ~50 行 |
| 游戏路由（/act 接口） | ~80 行 |
| **总计** | **~300 行** |

---

## 五、决策结论

| 决策 | 结论 | 理由 |
|---|---|---|
| 范式 | **对话流 + 轻量结构化外壳** | 内核是 LLM 单轮调用完成叙事+判定+更新；外壳用代码保证 JSON 解析和 infomation merge 的正确性 |
| 平台 | **原生 API（OpenAI SDK 兼容模式）** | 控制力最强、最轻量、无平台锁定、Invencia 核心流程简单不需要编排引擎 |
| 不用 | Coze / Dify / LangChain | 增加抽象层但不增加价值；Coze 封闭不适合长文本创意；Dify 对开发团队无优势 |

### 一言蔽之

> Invencia 的"智能体"本质上就是一个精心设计的 **System Prompt + 上下文组装函数 + JSON 解析器**，不需要任何 Agent 框架。

---

## 六、后续工作

- [ ] 搭建 AI 客户端封装（`service/ai_client.py`）
- [ ] 设计修仙世界 System Prompt 模板（存 t_world.system_prompt）
- [ ] 实现 infomation 增量 merge 逻辑
- [ ] 实现 `/game/act` 核心接口

---

*决策文档完成。下一步进入详细设计。*
