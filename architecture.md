# 无敌 (Invencia) —— 概要设计文档

> 版本：v1.0
> 日期：2026-05-23
> 前置文档：requirements.md（需求分析）、agent-architecture.md（智能体架构决策）

---

## 一、架构总览

```
┌─────────────────────────────────────────────────┐
│                  前端（浏览器）                    │
│                                                 │
│  ┌──────────┐  ┌──────────┐  ┌───────────────┐ │
│  │  主页     │  │ 登录/注册 │  │   游戏主界面    │ │
│  │ /        │  │ /login   │  │ /game/:cid    │ │
│  │ 免登录    │  │          │  │ ┌───────────┐ │ │
│  │          │  │          │  │ │ 对话区     │ │ │
│  │          │  │          │  │ │ 输入框     │ │ │
│  │          │  │          │  │ │ 角色面板   │ │ │
│  │          │  │          │  │ │ (侧边栏)   │ │ │
│  │          │  │          │  │ └───────────┘ │ │
│  └──────────┘  └──────────┘  └───────────────┘ │
│                                                 │
│  路由守卫：/game/* 需 JWT，否则弹登录框             │
└────────────────────┬────────────────────────────┘
                     │ HTTP + JSON
                     │ Authorization: Bearer <jwt>
┌────────────────────▼────────────────────────────┐
│               FastAPI 后端                       │
│                                                 │
│  ┌──────────┐  ┌──────────┐  ┌───────────────┐ │
│  │ world    │  │ auth     │  │ game          │ │
│  │ 模块     │  │ 模块     │  │ 模块          │ │
│  │          │  │          │  │               │ │
│  │ GET      │  │ POST     │  │ POST /act     │ │
│  │ /worlds  │  │ /register│  │ GET /messages │ │
│  │          │  │ /login   │  │               │ │
│  └──────────┘  └──────────┘  └───────┬───────┘ │
│                                      │         │
│  ┌───────────────────────────────────┤         │
│  │ character 模块                    │         │
│  │ GET  /characters                 │         │
│  │ POST /characters (调 Coze)       │         │
│  │ GET  /characters/:id             │         │
│  └──────────────────────────────────┘         │
│                                      │         │
│  ┌───────────────────────────────────┘         │
│  │ AI 接入层 (service/ai_client.py)             │
│  │  ┌─────────────────────────────┐            │
│  │  │ Coze Workflow API 调用      │            │
│  │  │ - 角色创建工作流             │            │
│  │  │ - 天道推演工作流             │            │
│  │  └─────────────────────────────┘            │
│  └─────────────────────────────────────────────┘
│                                      │
└──────────────────────────────────────┼────────┘
                                       │
┌──────────────────────┐  ┌───────────▼──────────┐
│  SQLite              │  │  Coze 平台            │
│  t_world             │  │  ├ 角色创建工作流      │
│  t_user              │  │  └ 天道推演工作流      │
│  t_character         │  │            │          │
│  t_message           │  │   DeepSeek / 千问     │
└──────────────────────┘  └───────────────────────┘
```

---

## 二、技术栈

| 层 | 技术 | 版本 | 说明 |
|---|---|---|---|
| 前端 | HTML + CSS + Vanilla JS | — | 零构建，单文件或少量文件 |
| 后端框架 | FastAPI | ≥ 0.110 | Python 异步 Web 框架 |
| ORM | SQLAlchemy | ≥ 2.0 | 或直接用 aiomysql/SQLite 驱动 |
| 数据库 | SQLite | 3 | 单文件，零配置 |
| 认证 | PyJWT + bcrypt | — | JWT 签发/验证，密码哈希 |
| AI 编排 | Coze 工作流 API | — | 两个工作流，API 触发模式 |
| AI 模型 | DeepSeek v4 / 通义千问 | — | 通过 Coze 配置，支持 fallback |
| 部署 | Docker / 直接运行 | — | 前端静态文件由 FastAPI 托管 |

---

## 三、页面结构（3 个视图）

根据需求分析优化：角色创建融合为弹窗，角色面板融合为侧边栏，减少页面维护。

| 视图 | 路由 | 认证 | 说明 |
|---|---|---|---|
| **主页** | `/` | 无 | 平台 Landing Page：世界展示 + 示例叙事 + "开始修仙"按钮 |
| **登录/注册** | `/login` | 无 | 登录表单 + 注册入口；也可主页弹窗实现 |
| **游戏主界面** | `/game/:character_id` | JWT | 核心视图，内含三个区域 |

### 游戏主界面内部结构

```
┌──────────────────────────────────────────────┐
│  导航栏                                       │
│  [无敌 Invencia]              [角色名] [面板]  │
├────────────────────┬─────────────────────────┤
│                    │                         │
│   对话区            │   角色面板（侧边栏）       │
│   (主区域)          │   - realm              │
│                    │   - power              │
│   [天道叙事...]     │   - origin             │
│   [玩家输入...]     │   - obsession          │
│   [天道叙事...]     │   - location           │
│                    │   - dao_heart          │
│                    │   - causality          │
│                    │   - relationships      │
│                    │   - inventory          │
│                    │   - summary            │
│                    │                         │
├────────────────────┴─────────────────────────┤
│  输入区                                       │
│  [________________________________] [发送]   │
│  [天道推演中...]          (Loading 指示器)     │
└──────────────────────────────────────────────┘
```

### 弹窗

| 弹窗 | 触发条件 | 内容 |
|---|---|---|
| **创建角色** | 登录后无角色 → 自动弹出 | 角色名 + 性别 + AI 生成 Loading → 生成后展示 infomation 预览 → "踏入仙途" |
| **登录/注册** | 主页点击"开始修仙"且未登录 | 登录表单 / 注册表单切换 |

> 设计原则：角色创建不需要单独页面——它是一个一次性的引导流程，弹窗完成即可。角色面板不是独立页面——玩家在游戏中随时查看，侧边栏最自然。

---

## 四、模块设计

### 4.1 后端模块

```
backend/
├── main.py                 # FastAPI 入口，路由注册
├── config.py               # 配置（DB路径、JWT密钥、Coze API）
├── middleware/
│   └── auth.py             # JWT 验证中间件
├── modules/
│   ├── world/
│   │   └── router.py       # GET /api/worlds
│   ├── auth/
│   │   ├── router.py       # POST /register, /login, /refresh
│   │   └── service.py      # 密码哈希、Token 签发
│   ├── character/
│   │   ├── router.py       # GET /characters, POST, GET /:id
│   │   └── service.py      # 角色 CRUD、调用 Coze 角色创建工作流
│   └── game/
│       ├── router.py       # POST /:character_id/act, GET /:character_id/messages
│       └── service.py      # 上下文组装、调用 Coze 天道推演工作流、infomation merge
├── models/
│   ├── world.py            # t_world ORM 模型
│   ├── user.py             # t_user ORM 模型
│   ├── character.py        # t_character ORM 模型
│   └── message.py          # t_message ORM 模型
├── service/
│   └── ai_client.py        # Coze API 封装（调用工作流、重试、fallback）
└── static/                 # 前端静态文件
    ├── index.html          # 主页
    ├── login.html          # 登录/注册
    ├── game.html           # 游戏主界面
    ├── css/
    │   └── style.css       # 全局样式（黑底古风）
    └── js/
        ├── router.js       # 前端路由 + JWT 守卫
        ├── api.js          # HTTP 请求封装
        └── game.js         # 游戏界面交互逻辑
```

### 4.2 模块职责

| 模块 | 职责 | 依赖 |
|---|---|---|
| **world** | 返回可用世界列表（主页展示用） | t_world |
| **auth** | 注册、登录、Token 签发/刷新/验证 | t_user, PyJWT, bcrypt |
| **character** | 角色 CRUD，创建时调 Coze 工作流生成出身 | t_character, ai_client |
| **game** | 核心游戏循环：取上下文 → 调 Coze → merge infomation → 存消息 | t_character, t_message, ai_client |
| **ai_client** | 封装 Coze 工作流 API 调用（重试、超时、fallback） | Coze API |

---

## 五、API 设计（汇总）

### 5.1 完整接口表

| 方法 | 路径 | 认证 | 请求体 | 响应 data | 说明 |
|---|---|---|---|---|---|
| GET | `/api/worlds` | 无 | — | `[{id, code, name, agent_name, description, cover_config}]` | 主页世界列表 |
| POST | `/api/auth/register` | 无 | `{username, password}` | `{token, user}` | 注册成功自动返回 JWT |
| POST | `/api/auth/login` | 无 | `{username, password}` | `{token, user}` | 登录返回 JWT |
| POST | `/api/auth/refresh` | JWT | — | `{token}` | Token 续期 |
| GET | `/api/characters` | JWT | — | `[{id, name, gender, realm_summary, world_id, updated_at}]` | 角色列表（简要信息） |
| POST | `/api/characters` | JWT | `{name, gender}` | `{id, name, gender, infomation}` | 创建角色（调 Coze） |
| GET | `/api/characters/:id` | JWT | — | `{id, name, gender, infomation, world_id}` | 角色详情（含完整 infomation） |
| POST | `/api/game/:character_id/act` | JWT | `{input}` | `{narrative, hook, infomation}` | **核心接口**：发送决策，获取叙事 |
| GET | `/api/game/:character_id/messages` | JWT | `?before_id=&limit=50` | `{messages: [{id, type, content, created_at}]}` | 对话历史（分页） |

### 5.2 统一响应结构

```json
// 成功
{ "code": 0, "data": { ... }, "message": "ok" }

// 失败
{ "code": 40001, "data": null, "message": "用户名已存在" }
```

### 5.3 错误码规划

| code | 含义 |
|---|---|
| 0 | 成功 |
| 40001 | 参数校验失败 |
| 40100 | 未登录 / Token 过期 |
| 40101 | 用户名或密码错误 |
| 40300 | 无权访问该角色 |
| 40400 | 资源不存在 |
| 50000 | 服务端错误 |
| 50001 | AI 调用失败（可重试） |
| 50002 | AI 调用超时 |

---

## 六、核心数据流

### 6.1 角色创建流程

```
前端                          FastAPI                      Coze                  LLM
 │                              │                           │                    │
 │  POST /api/characters        │                           │                    │
 │  {name, gender}              │                           │                    │
 │─────────────────────────────>│                           │                    │
 │                              │  调 Coze 角色创建工作流      │                    │
 │                              │──────────────────────────>│                    │
 │                              │                           │  组装 Prompt       │
 │                              │                           │──────────────────>│
 │                              │                           │                    │
 │                              │                           │   infomation JSON  │
 │                              │                           │<──────────────────│
 │                              │                           │                    │
 │                              │  返回 infomation           │                    │
 │                              │<──────────────────────────│                    │
 │                              │                           │                    │
 │                              │  INSERT t_character        │                    │
 │                              │  （含 infomation）          │                    │
 │                              │                           │                    │
 │  {character + infomation}    │                           │                    │
 │<─────────────────────────────│                           │                    │
```

### 6.2 天道推演流程（核心游戏循环）

```
前端                          FastAPI                      Coze                  LLM
 │                              │                           │                    │
 │  POST /game/:id/act          │                           │                    │
 │  {input: "我悄悄绕到..."}      │                           │                    │
 │─────────────────────────────>│                           │                    │
 │                              │  1. 鉴权（JWT + 角色归属）   │                    │
 │                              │  2. SELECT infomation      │                    │
 │                              │     FROM t_character       │                    │
 │                              │  3. SELECT 最近 20 条消息    │                    │
 │                              │     FROM t_message         │                    │
 │                              │                           │                    │
 │                              │  调 Coze 天道推演工作流      │                    │
 │                              │  {infomation, messages,    │                    │
 │                              │   world_system_prompt,     │                    │
 │                              │   user_input}              │                    │
 │                              │──────────────────────────>│                    │
 │                              │                           │  组装完整 Prompt    │
 │                              │                           │──────────────────>│
 │                              │                           │                    │
 │                              │                           │  {narrative,       │
 │                              │                           │   hook,            │
 │                              │                           │   info_changes}    │
 │                              │                           │<──────────────────│
 │                              │                           │                    │
 │                              │  返回 {narrative,          │                    │
 │                              │         hook,              │                    │
 │                              │         info_changes}      │                    │
 │                              │<──────────────────────────│                    │
 │                              │                           │                    │
 │                              │  4. INSERT t_message       │                    │
 │                              │     (type=user, input)     │                    │
 │                              │  5. INSERT t_message       │                    │
 │                              │     (type=assistant,       │                    │
 │                              │      narrative+hook)       │                    │
 │                              │  6. MERGE info_changes     │                    │
 │                              │     → UPDATE t_character   │                    │
 │                              │     .infomation            │                    │
 │                              │                           │                    │
 │  {narrative, hook,           │                           │                    │
 │   infomation(更新后)}         │                           │                    │
 │<─────────────────────────────│                           │                    │
```

---

## 七、前端路由设计

```
/                    → index.html    （主页，免登录）
/login               → login.html    （登录/注册）
/game/:character_id  → game.html     （游戏主界面，需 JWT）
```

### 路由守卫逻辑

```javascript
// router.js 伪代码
function guard(route) {
    const publicRoutes = ['/', '/login'];
    if (publicRoutes.includes(route)) return;

    const token = localStorage.getItem('jwt');
    if (!token || isExpired(token)) {
        // 未登录 → 跳主页，弹登录框
        navigateTo('/');
        showLoginModal();
    }
}
```

---

## 八、数据库设计要点

四张表（详见 project-status.md 数据模型）：

| 表 | 核心字段 | 说明 |
|---|---|---|
| t_world | code, name, agent_name, system_prompt, cover_config | MVP 硬编码一条修仙世界 |
| t_user | username, password_hash | 用户认证 |
| t_character | user_id, world_id, name, gender, infomation(JSON) | 角色，infomation 10 字段全叙事 |
| t_message | conversation_id(=character_id), type, content, metadata(JSON) | 对话历史 + 事件记录 |

关键索引：
- `t_character(user_id)` — 查用户的角色列表
- `t_message(conversation_id, created_at)` — 按时间取最近消息

---

## 九、Coze 工作流概要

两个工作流，均通过 Coze Workflow API 触发：

| 工作流 | 触发时机 | 输入 | 输出 |
|---|---|---|---|
| **角色创建** | POST /api/characters | name, gender | infomation (10 字段 JSON) |
| **天道推演** | POST /api/game/:id/act | infomation, messages[], world_prompt, user_input | narrative, hook, info_changes |

> 详细节点设计（LLM 配置、Prompt 全文、代码插件逻辑）见详细设计文档。

---

## 十、部署架构

```
┌─────────────────────────────────┐
│  服务器 / VPS                     │
│                                 │
│  FastAPI (uvicorn)              │
│  ├── 后端 API (:8000)            │
│  └── 静态文件 (HTML/CSS/JS)      │
│                                 │
│  SQLite 文件 (data/invencia.db)  │
└─────────────────────────────────┘
         │
         │ HTTPS (nginx 反代)
         │
    [用户浏览器]
```

MVP 阶段最简单部署：
```bash
# 服务器上
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
# nginx 反代 80/443 → 8000
```

---

## 十一、待确认问题

| # | 问题 | 当前假设 |
|---|---|---|
| 1 | Coze 工作流 API 是否支持外部 HTTP 触发？还是需要 Webhook 模式？ | 假设支持 REST API 触发，待验证 |
| 2 | infomation merge 是后端做还是 Coze 代码节点做？ | **后端做**——Coze 代码节点只负责解析 JSON，merge 逻辑在 FastAPI |
| 3 | 前端三页面是三个独立 HTML 还是 SPA？ | MVP 建议三个独立 HTML，路由简洁，零框架依赖 |
| 4 | 主页的"示例叙事"是写死的静态文本，还是调一次 AI 实时生成？ | **静态文本**——写在 t_world.cover_config 里，首屏秒开 |

---

*概要设计 v1.0 完成。下一步：详细设计（Coze 工作流节点配置 + Prompt 模板全文）。*
