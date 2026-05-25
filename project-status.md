# 无敌 (Invencia) —— 项目状态总览

> 版本：v2.0
> 日期：2026-05-25
> 用途：新会话快速加载上下文——关键决策、已完成部分、待办事项、架构思路、文件记录一览。

---

## 一、项目定位

**无敌 (Invencia)** —— 叙事驱动的文字 RPG 平台，承载多个 AI 智能体"世界"。

| 属性 | 值 |
|---|---|
| MVP 首个世界 | **修仙** |
| 世界名 | **玄天界**（三字） |
| 驱动 AI | **天道** 智能体（Dify Chatflow Agent） |
| 交互方式 | 自由文本输入，AI 实时叙事，千人千命 |
| 核心 slogan | 千人千命，天道为笔 |
| GitHub | `git@github.com:XXXYJade17/invencia.git` |
| 文档分支 | `docs`（全部 .md），`master` 仅 `.gitignore` |

---

## 二、关键决策记录

| # | 决策 | 结论 | 日期 |
|---|------|------|------|
| 1 | 平台名称 | 无敌 (Invencia)，修仙是 MVP 首个世界 | 初期 |
| 2 | 世界观 | 玄天界，五域（苍玄/焚天/无尘/玄冥/混元） | 初期 |
| 3 | 境界体系 | 凡人→练气→筑基→金丹→元婴→化神→合体→渡劫→大乘→飞升 | 初期 |
| 4 | 交互模式 | 自由文本输入，AI 驱动叙事，开放式钩子结尾 | 初期 |
| 5 | 页面结构 | 2 视图（主页 + 游戏主界面）+ 3 弹窗（登录/角色列表/创建角色） | v1.5 |
| 6 | 登录/注册 | 统一弹窗（非独立页面） | v2.2 |
| 7 | 多角色 | MVP 上限 3 个 | v2.1 |
| 8 | AI 编排平台 | **Dify**（Workflow + Chatflow Agent，原生 function calling） | 2026-05-25 |
| 9 | 技术栈 | 前端 HTML+CSS+JS / 后端 FastAPI+Python / SQLite / Dify | 初期 |
| 10 | 文档体系 | 五文档：灵感 → 需求 → 概要设计 → 详细设计(12文件) → docs-guide | v2.5 |
| 11 | 编码标准 | UTF-8 BOM + CRLF + 三反引号代码块（见 docs-guide §3.0） | v1.1 |
| 12 | 渡劫 MVP 策略 | 仅叙事，不执行永久死亡 | 初期 |
| 13 | 角色创建 | **凡人模板**：单 Prompt，spiritual_roots: []，灵根在游戏中觉醒 | 2026-05-25 |
| 14 | 灵根系统 | **Dify Code Tool**：纯代码按概率表抽取，Agent 自主判定调用时机 | 2026-05-25 |
| 15 | infomation 结构 | 分层结构（basic_info/cultivation/physique/mind_spirit + 数组字段），删除 obsession/summary | 2026-05-25 |
| 16 | 天道推演 | **Agent 单 System Prompt + Tools**，LLM 自主调用工具，非手动路由 | 2026-05-25 |
| 17 | Prompt 管理 | 后端 Git 管理 `backend/prompts/*.txt`，运行时通过 Dify API 参数传入 | 2026-05-25 |

---

## 三、已完成部分

### 3.1 文档体系（全部完成 ✅）

| 文件 | 版本 | 状态 | 说明 |
|---|---|---|---|
| `design-inspiration.md` | — | ✅ | 玄天界世界观、境界体系、核心玩法愿景 |
| `requirements.md` | v2.5 | ✅ | 22 条 FR（分模块）、5 条 NFR |
| `architecture.md` | v1.1 | ✅ | 技术选型(Dify)、架构分层、模块划分、API 路径、DB 设计 |
| `docs-guide.md` | v1.1 | ✅ | 四层文档边界、格式强约束、检查清单 |
| `project-status.md` | v2.0 | ✅ | 本文件——会话上下文加载 |
| `detailed-design/` | — | ✅ | **12 文件**，完整详细设计 |

### 3.2 详细设计文件清单（12 文件）

| # | 文件 | 版本 | 核心内容 |
|---|------|------|----------|
| — | `README.md` | v2.0 | 索引 + 阅读顺序 |
| 1 | `01-database.md` | — | DDL、索引、WAL、迁移 |
| 2 | `02-auth.md` | — | bcrypt + JWT + 中间件 |
| 3 | `03-characters.md` | v2.1 | CRUD + AI 生成编排 + merge 算法 + verify |
| 4 | `04-game-engine.md` | v2.0 | 游戏循环 + Dify API 封装 + 工具调度说明 |
| 5 | `05-dify-workflows.md` | v4.0 | Workflow(角色创建) + Chatflow Agent(天道推演) + API 封装 |
| 5a | `05a-system-prompt-char-create.md` | v4.0 | 角色创建单 Prompt（凡人模板） |
| 5b | `05b-system-prompt-narrative.md` | v4.0 | 天道推演 Agent System Prompt + 工具感知 |
| 5c | `05c-tool-spiritual-roots.md` | v2.0 | 灵根觉醒 Dify Code Tool（概率表 + 实现） |
| 6 | `06-api-specs.md` | — | 14 个 API JSON 示例 |
| 7 | `07-frontend.md` | — | HTML 骨架 + CSS 黑底古风 + JS 模块 |
| 8 | `08-deployment.md` | — | Nginx + Uvicorn + .env |

### 3.3 需求分析 FR 总览

**主页（3）**：FR-HOME-001 平台主页 / 002 登录入口 / 003 免登录保护

**认证（4）**：FR-AUTH-001 注册 / 002 登录 / 003 续期 / 004 持久化

**角色（5）**：FR-CHAR-001 角色列表 / 002 创建(AI) / 003 面板 / 004 面板更新 / 005 按世界查询

**游戏核心（7）**：FR-GAME-001 自由输入 / 002 AI 叙事 / 003 战斗 / 004 渡劫 / 005 info 维护 / 006 历史展示 / 007 历史持久化

**辅助（2）**：FR-AUX-001 错误提示 / 002 Loading

**NFR（5）**：模型响应、并发、安全、界面、数据一致性。共 **22 FR + 5 NFR**。

### 3.4 页面结构

```
2 视图：
  /                       主页（Landing Page，免登录）
  /game/:character_id     游戏主界面（需认证）

3 弹窗：
  登录/注册弹窗           主页"开始修仙"触发
  角色列表弹窗             登录后自动弹出
  创建角色弹窗             角色列表中触发
```

---

## 四、待办事项

### 4.1 文档（全部完成 ✅）

- [x] `architecture.md`（概要设计 v1.1，Dify 平台）
- [x] `detailed-design/`（12 文件完整详细设计）

### 4.2 开发 Phase（来自 requirements.md §七）

| Phase | 内容 | 预估 | 状态 |
|---|---|---|---|
| Phase 1 | 骨架搭建（项目初始化、DB 建表、前端骨架） | 2-3 天 | ⬜ 待开始 |
| Phase 2 | 主页 + 认证（Landing Page、注册/登录 API） | 2-3 天 | ⬜ 待开始 |
| Phase 3 | 角色创建（AI 生成 infomation、角色面板 UI） | 2-3 天 | ⬜ 待开始 |
| Phase 4 | 核心游戏循环（叙事 API、System Prompt、对话 UI） | 3-5 天 | ⬜ 待开始 |
| Phase 5 | 打磨上线（动画、错误处理、性能、部署） | 2-3 天 | ⬜ 待开始 |

### 4.3 Dify 平台搭建

- [ ] Docker 部署 Dify 实例
- [ ] 创建 Workflow `char-creation`（按 `05-dify-workflows.md §四` 配置）
- [ ] 创建 Chatflow `tiandao-narrative`（按 `§五` 配置 Agent + Tools）
- [ ] 注册 Code Tool `awaken-spiritual-roots`（按 `05c-tool-spiritual-roots.md`）
- [ ] 上传玄天界知识库文档

---

## 五、架构思路概览

### 5.1 整体架构

```
┌─────────────────────────────────────────────────────┐
│                前端 (HTML+CSS+JS SPA)                  │
│  Hash 路由：/ → 主页  |  /game/:id → 游戏界面         │
│  弹窗：登录/注册 | 角色列表 | 创建角色                  │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP (JSON)
┌──────────────────────┴──────────────────────────────┐
│              FastAPI 后端 (Python)                     │
│  ┌─────────┐ ┌──────────┐ ┌────────────────────┐    │
│  │ 认证模块 │ │ 角色模块  │ │ 游戏核心循环        │    │
│  │ 注册/登录│ │ CRUD+AI  │ │ 叙事+info merge    │    │
│  └─────────┘ └──────────┘ └─────────┬──────────┘    │
│                                      │                │
│                          ┌───────────┴───────────┐   │
│                          │     SQLite (WAL)       │   │
│                          │  4 表: users/chars/    │   │
│                          │  worlds/messages       │   │
│                          └───────────────────────┘   │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP (Dify API)
┌──────────────────────┴──────────────────────────────┐
│                  Dify 平台 (Docker)                    │
│                                                       │
│  ┌─────────────────────┐  ┌────────────────────────┐ │
│  │ Workflow             │  │ Chatflow               │ │
│  │ char-creation        │  │ tiandao-narrative      │ │
│  │                      │  │                        │ │
│  │ [代码:抽签]→[LLM]    │  │ [Agent: 天道]          │ │
│  │ →[代码:校验]         │  │  ├─ System Prompt      │ │
│  │                      │  │  └─ Tools:             │ │
│  │ 输出: infomation     │  │     awaken-roots       │ │
│  └─────────────────────┘  │     (future...)         │ │
│                            │  输出: narrative+hooks  │ │
│                            │  +info_changes          │ │
│                            └────────────────────────┘ │
│                                                       │
│              国产大模型 (DeepSeek / Qwen)              │
└──────────────────────────────────────────────────────┘
```

### 5.2 Agent 工具调用流程

```
玩家输入 → Dify Chatflow
  → Agent 推理：需要调用工具？
    ├─ 是（如灵根觉醒） → 调用 awaken-spiritual-roots → 获取结果 → 融入叙事
    └─ 否 → 直接输出叙事
  → 返回: { narrative, hooks, info_changes, metadata }
  → 后端 merge_infomation() → 持久化 → 返回前端
```

### 5.3 infomation 结构（v3.0）

```
infomation
├── basic_info {appearance, personality, origin}    标量覆盖
├── cultivation {realm, power, dao_heart, spiritual_roots[]}  标量覆盖
├── physique {condition, traits[]}                  标量覆盖
├── mind_spirit {mental_state, spiritual_power}     标量覆盖
├── inventory[] {name,type,grade,quantity,desc}     数组按name合并
├── techniques[] {name,type,mastery,desc}           数组按name合并
├── relationships[] {name,identity,relationship,attitude,notes} 数组按name合并
├── causality[] {event,desc,status}                 数组按event合并
└── location                                        标量覆盖
```

**Merge 算法**：标量直接覆盖；数组按 name/event 匹配→更新或追加；inventory quantity=0 删除。

### 5.4 灵根体系

| 稀有度 | 概率 | 包含 |
|--------|------|------|
| common | 70% | 伪灵根 + 三灵根 |
| uncommon | 18% | 双灵根 |
| rare | 10% | 天灵根 + 异灵根（风雷冰） |
| legendary | 1.5% | 混沌灵根 + 阴阳灵根 |
| cursed | 0.5% | 天漏之体 |

灵根在角色创建时为空（`spiritual_roots: []`），由 Agent 在叙事中自主调用 `awaken-spiritual-roots` 工具觉醒。

---

## 六、重要文件修改记录（本次会话）

| 文件 | 动作 | 版本变更 | 关键内容 |
|------|------|----------|----------|
| `architecture.md` | 新建 → 更新 | v1.0 → v1.1 | Coze→Dify 切换，技术栈更新 |
| `detailed-design/05-dify-workflows.md` | **新建**（替换 05-coze-workflows.md） | v4.0 | Dify Workflow + Chatflow Agent 配置 |
| `detailed-design/05a-...-char-create.md` | 重写 | v3.0 → v4.0 | 单 Prompt，凡人模板，删除 4 节点设计 |
| `detailed-design/05b-...-narrative.md` | 重写 | v3.0 → v4.0 | Agent 单 Prompt + 工具感知，删除手动路由 |
| `detailed-design/05c-...-spiritual-roots.md` | 更新 | v1.0 → v2.0 | Dify Code Tool，Agent 自主调用 |
| `detailed-design/04-game-engine.md` | 重写 | v1.1 → v2.0 | Dify API 调用，删除手动工具调度 |
| `detailed-design/03-characters.md` | 更新 | v2.0 → v2.1 | spiritual_roots 字段，Dify 引用 |
| `detailed-design/README.md` | 更新 | v1.1 → v2.0 | 索引更新，Coze→Dify |
| `docs-guide.md` | 更新 | — | Coze→Dify 替换 |
| `project-status.md` | 重写 | v1.0 → v2.0 | 本文件——全量上下文更新 |

---

## 七、Git 提交记录（最近 5 条）

```
b68b3fc docs: 详细设计完成 + 平台切换 Coze→Dify
f3ca05b docs: add project-status.md v1.0 - session handoff context loader
a113126 docs: update docs-guide.md to v1.1 - add format enforcement rules (§3.0)
99f8cd6 docs: 修复 design-inspiration.md 代码块反引号格式——单引号改为三引号
74ee573 docs: 最终审查——三份文档统一 UTF-8 BOM + CRLF、零乱码、零越界术语
```

---

## 八、编码与格式速查

| 规则 | 说明 |
|------|------|
| 编码 | UTF-8 with BOM（`EF BB BF`） |
| 行尾 | CRLF（`\r\n`） |
| 代码块 | 三反引号 ```，禁止 4 空格缩进 |
| 缩进 | 2 空格，禁止 Tab |
| 禁 0x3F | 中文乱码标志字节，提交前 hex 验证 |

**安全读**：`[System.IO.File]::ReadAllText(path, [System.Text.UTF8Encoding]::new($true))`

**安全写**：`[System.IO.File]::WriteAllText(path, content, [System.Text.UTF8Encoding]::new($true))`

---

## 九、AI 提示词文件规划

```
backend/prompts/
├── char_create.txt         角色创建 System Prompt（单文件）
├── narrative.txt            天道推演 Agent System Prompt（单文件）
└── awakening.txt            觉醒叙事补充 Prompt（可选）
```

运行时后端读取 → Dify API `inputs.system_prompt` 传入。

---

## 十、环境变量清单（规划）

```env
DIFY_API_BASE=https://api.dify.ai         # 或自部署地址
DIFY_API_KEY=dify-chatflow-key
DIFY_WF_API_KEY=dify-workflow-key
DIFY_APP_CHAR_CREATE=app-id               # Workflow
DIFY_APP_NARRATIVE=app-id                 # Chatflow

# 多模型备选（Dify 侧配置）
# LLM_MODEL=deepseek-chat
# LLM_FALLBACK=qwen-turbo

JWT_SECRET=your-secret
JWT_EXPIRE_DAYS=7
DB_PATH=./data/invencia.db
```

---

*新会话加载本文档即可恢复全部上下文。下一步：搭建 Dify 平台 + 开始 Phase 1 编码。*
