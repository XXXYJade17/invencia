# 无敌 (Invencia) —— 详细设计

> 版本：v2.0
> 日期：2026-05-25
> 前置文档：architecture.md（概要设计 v1.1，Dify 平台）

---

> **文档边界**：本文件夹为详细设计，回答"每步怎么实现"。包含 Dify Workflow/Agent 配置、System Prompt 全文及设计思路、DDL 语句、API JSON 示例、infomation merge 算法等。

---

## 文件索引

| # | 文件 | 内容 | 前置依赖 |
|---|------|------|----------|
| 1 | [01-database.md](./01-database.md) | DDL 建表语句、索引、WAL 配置、迁移策略 | architecture.md 六 |
| 2 | [02-auth.md](./02-auth.md) | 密码哈希方案、JWT 签发/验证/续期、认证中间件 | 01-database.md |
| 3 | [03-characters.md](./03-characters.md) | 角色 CRUD 实现、AI 生成编排、infomation merge 算法 | 01-database.md, 05-dify-workflows.md |
| 4 | [04-game-engine.md](./04-game-engine.md) | 核心游戏循环、上下文组装、叙事处理、战斗/渡劫判定 | 03-characters.md, 05-dify-workflows.md |
| 5 | [05-dify-workflows.md](./05-dify-workflows.md) | Dify Workflow（角色创建）+ Chatflow Agent（天道推演）配置、后端 API 封装 | architecture.md 八 |
| 5a | [05a-system-prompt-char-create.md](./05a-system-prompt-char-create.md) | **角色创建**：单 Prompt，凡人模板，infomation 结构 | 05-dify-workflows.md |
| 5b | [05b-system-prompt-narrative.md](./05b-system-prompt-narrative.md) | **天道推演**：Agent 单 Prompt + 工具感知 + 输出规范 | 05-dify-workflows.md |
| 5c | [05c-tool-spiritual-roots.md](./05c-tool-spiritual-roots.md) | **灵根觉醒工具**：Dify Code Tool、概率表、Agent 集成 | 05-dify-workflows.md |
| 6 | [06-api-specs.md](./06-api-specs.md) | 全部 14 个 API 的请求/响应 JSON 完整示例 | architecture.md 五 |
| 7 | [07-frontend.md](./07-frontend.md) | HTML 页面结构、CSS 关键样式、JS 组件逻辑 | architecture.md 三 |
| 8 | [08-deployment.md](./08-deployment.md) | Nginx 配置、Uvicorn 启动参数、环境变量清单 | architecture.md 九 |

## 阅读顺序

```
01-database.md                 <- 基础设施，最先阅读
  ├── 02-auth.md               <- 认证依赖用户表
  ├── 05-dify-workflows.md     <- Dify 工作流 + Agent
  │     ├── 05a-...char-create.md  <- 角色创建 Prompt
  │     └── 05b-...narrative.md    <- 天道推演 Prompt
  │     └── 05c-...spiritual-roots.md <- 灵根觉醒工具
  ├── 03-characters.md         <- 依赖数据库 + Dify
  ├── 04-game-engine.md        <- 依赖角色 + Dify + Prompt
  ├── 06-api-specs.md          <- 依赖上述全部模块
  ├── 07-frontend.md           <- 依赖 API 规范
  └── 08-deployment.md         <- 最后阅读
```

## 格式规范

- 编码：UTF-8 BOM + CRLF
- 代码块：三反引号 ```
- 缩进：2 空格，禁止 Tab
- 标题层级：## → ### → ####

---

*详细设计索引 v2.0。按编号顺序阅读。*

