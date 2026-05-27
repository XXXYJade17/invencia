# 无敌 (Invencia) —— 详细设计

> 版本：v3.1
> 日期：2026-05-25
> 前置文档：architecture.md（概要设计 v1.1，Dify 平台）

---

> **文档边界**：本文件夹为详细设计，回答"每步怎么实现"。包含 Dify Workflow/Agent 配置、DDL 语句、API JSON 示例、角色信息合并算法等。
>
> **玄天界设定与提示词**已独立为 [`xuantian-realm/`](./xuantian-realm/) 子目录。

---

## 文件索引

### 技术设计

| # | 文件 | 内容 | 前置依赖 |
|---|------|------|----------|
| 1 | [01-database.md](./01-database.md) | DDL 建表语句、索引、WAL 配置、迁移策略 | architecture.md 六 |
| 2 | [02-auth.md](./02-auth.md) | 密码哈希方案、JWT 签发/验证/续期、认证中间件 | 01-database.md |
| 3 | [03-characters.md](./03-characters.md) | 角色 CRUD 实现、AI 生成编排、角色信息合并算法 | 01-database.md, 05-dify-workflows.md |
| 4 | [04-game-engine.md](./04-game-engine.md) | 核心游戏循环、上下文组装、叙事处理、战斗/渡劫判定 | 03-characters.md, 05-dify-workflows.md |
| 5 | [05-dify-workflows.md](./05-dify-workflows.md) | Dify Workflow（角色创建）+ Chatflow Agent（天道推演）配置、后端 API 封装 | architecture.md 八 |
| 6 | [06-api-specs.md](./06-api-specs.md) | 全部 14 个 API 的请求/响应 JSON 完整示例 | architecture.md 五 |
| 7 | [07-frontend.md](./07-frontend.md) | HTML 页面结构、CSS 关键样式、JS 组件逻辑 | architecture.md 三 |
| 8 | [08-deployment.md](./08-deployment.md) | Nginx 配置、Uvicorn 启动参数、环境变量清单 | architecture.md 九 |

### 玄天界内容

| # | 文件 | 内容 |
|---|------|------|
| 9 | [xuantian-realm/](./xuantian-realm/) | **玄天界全部设定与提示词（武道化 v2.0）**：世界观、角色模板、Prompt、工具 |

详见 [xuantian-realm/README.md](./xuantian-realm/README.md)。

---

## 阅读顺序

```
01-database.md                 <- 基础设施，最先阅读
  ├── 02-auth.md               <- 认证依赖用户表
  ├── 05-dify-workflows.md     <- Dify 工作流 + Agent
  ├── 03-characters.md         <- 依赖数据库 + Dify
  ├── 04-game-engine.md        <- 依赖角色 + Dify + Prompt
  ├── 06-api-specs.md          <- 依赖上述全部模块
  ├── 07-frontend.md           <- 依赖 API 规范
  ├── 08-deployment.md         <- 最后阅读
  └── xuantian-realm/          <- 玄天界内容层（角色模板、Prompt、工具）
        ├── xuantian-realm/setting/ → 世界观（拆分5文件）
        ├── 02-char-template.md <- 角色模板
        ├── 03-prompts.md      <- Prompt 合集
        └── 04-tools.md        <- 工具设计
```

## 格式规范

- 编码：UTF-8 BOM + CRLF
- 代码块：三反引号 ```
- 缩进：2 空格，禁止 Tab
- 标题层级：## → ### → ####

---

*详细设计索引 v3.0。按编号顺序阅读。*