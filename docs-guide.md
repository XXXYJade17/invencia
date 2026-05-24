# 无敌 (Invencia) —— 文档体系规则

> 版本：v1.1
> 日期：2026-05-24
> 用途：定义所有文档的类型、范围、边界和编写规范。每次修改文档前必须参考本文档。

---

## 一、文档类型与边界

### 1.1 四层文档体系

```
design-inspiration.md    灵感层  → "做成什么样"
requirements.md          需求层  → "做什么"
architecture.md          概要设计 → "用什么技术做"
detailed-design.md       详细设计 → "每步怎么实现"
```

### 1.2 各文档的严格边界

#### design-inspiration.md（灵感文档）

| ✅ 包含 | ❌ 不包含 |
|---|---|
| 世界观设定 | 功能列表 |
| 玩法愿景 | 技术选型 |
| 核心体验描述 | API 设计 |
| 美术/UI 风格方向 | 数据库表结构 |
| 为什么做这个项目 | 开发计划 |

#### requirements.md（需求分析）

| ✅ 包含 | ❌ 不包含 |
|---|---|
| 功能需求（FR-xxx：用户能做什么） | 实现方式（用什么技术） |
| 非功能需求（性能/安全/体验指标） | API 路径和请求格式 |
| 用户操作流程（先点哪里后点哪里） | 数据库表结构、字段类型 |
| 页面路由和认证要求 | Prompt 模板全文 |
| 数据存储需求（"需要存什么"） | 具体代码实现 |
| 输入输出业务规则 | Coze/Dify 工作流节点配置 |

> **核心原则：需求分析回答"做什么"，不回答"怎么做"。**

#### architecture.md（概要设计）

| ✅ 包含 | ❌ 不包含 |
|---|---|
| 技术选型及理由 | 逐行代码 |
| 架构分层图 | Prompt 精确措辞 |
| 模块划分与职责 | Coze 节点拖拽步骤 |
| 数据流（时序图） | 数据库 DDL |
| API 路径与方法定义 | CSS 样式细节 |
| 数据库表设计 | 前端组件实现 |

#### detailed-design.md（详细设计）

| ✅ 包含 | ❌ 不包含 |
|---|---|
| Coze 工作流节点配置 | 业务需求描述（那是需求的事） |
| System Prompt 全文 | 为什么要做（那是灵感的事） |
| 代码插件具体实现 | — |
| 数据库 DDL 语句 | — |
| API 请求/响应 JSON 示例 | — |
| infomation merge 算法 | — |

---

## 二、文档存放规则

### 2.1 分支策略

```
master 分支  → 代码（当前为空）
docs 分支    → 全部文档
```

- 所有 .md 文档仅在 docs 分支维护
- master 分支仅保留 .gitignore 等工程文件
- 文档更新：切换到 docs 分支 → 修改 → commit → push

### 2.2 文件命名

| 规则 | 示例 |
|---|---|
| 使用英文短横线命名 | `requirements.md` |
| 禁止中文文件名 | ❌ `需求分析.md` |
| 禁止空格 | ❌ `design inspiration.md` |

---

## 三、编写规范

### 3.0 格式强制要求（项目级）

以下规则适用于本项目所有 Markdown 文档，**每次编辑必须严格遵守**，提交前逐项自查。

| # | 规则 | 说明 |
|---|------|------|
| 1 | **UTF-8 with BOM** | 文件必须以 `EF BB BF` 开头。写入时必须使用 `[System.Text.UTF8Encoding]::new($true)` 或 Python `encoding='utf-8-sig'` |
| 2 | **CRLF 行尾** | 所有行尾必须是 `\r\n`，禁止混入单独的 `\n` |
| 3 | **三反引号代码块** | 代码块、JSON、Mermaid 等一律使用三个反引号 ``` 包裹，禁止缩进式代码块（4 空格） |
| 4 | **无多余空行** | 代码块首尾不得有空行；章节之间至多 1 个空行；文件末尾恰好 1 个空行 |
| 5 | **缩进规则** | 使用 2 空格缩进列表嵌套；禁止 Tab 字符；表格对齐空格不强制 |
| 6 | **禁止 0x3F 字节** | 文件不得出现 `3F` 字节（即 `?` 被错误编码后的产物），提交前用 hex 工具验证 |

**验证命令**：

```powershell
# 检查 BOM
$bytes = [System.IO.File]::ReadAllBytes('path/to/file.md')
if ($bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) { Write-Host "BOM OK" }

# 检查 0x3F 污染
$bad = ($bytes | Where-Object { $_ -eq 0x3F }).Count
if ($bad -gt 0) { Write-Host "WARNING: $bad 0x3F bytes found" }
```

**安全写入模板（Python）**：

```python
import os
path = 'D:/Project/docs/invencia/FILE.md'
content = "..."  # 所有换行用 \r\n
with open(path, 'w', encoding='utf-8-sig', newline='') as f:
    f.write(content)
```

### 3.1 通用规范

- 标题层级：`##` 一级章节，`###` 二级，`####` 三级
- 功能需求编号：`FR-{MODULE}-{NNN}`（如 FR-GAME-001）
- 表格使用 Markdown 原生语法，不嵌套 HTML
- 禁止在文档中使用实现术语（如 JWT、bcrypt、SQLite、FastAPI）——仅允许在详细设计中出现

### 3.2 FR 编写规范

```
#### FR-MODULE-NNN 功能名称
- **输入**：用户提供什么
- **规则**：系统如何处理
- **输出**：系统返回什么
- **异常**：出错时如何处理
```

- 规则中**禁止出现实现术语**（如 JWT、bcrypt、SQLite、FastAPI）
- 用业务语言描述（如"登录凭证"而非"JWT Token"）
- 不指定具体数值范围除非是业务约束（如"密码 6-32 字符"）

### 3.3 版本管理

- 每次修改后更新版本号
- 版本号格式：v{主版本}.{次版本}
  - 主版本：文档结构调整（章节增删）
  - 次版本：内容修改（FR 增删改、措辞调整）
- 在文档头部维护变更记录（最近 3 条）

---

## 四、技术选型速查

> 以下为已决策的技术方向，供文档编写时参考（不要在需求文档中引用）。

| 决策 | 选择 |
|---|---|
| 前端 | 纯 HTML + CSS + Vanilla JS |
| 后端 | Python |
| 数据库 | 单文件数据库 |
| AI 编排 | Coze 工作流 |
| AI 模型 | 国产大模型（兼容 OpenAI SDK） |
| 部署 | 自部署 |
| 认证 | 登录凭证（有过期时间） |

---

## 五、检查清单

每次修改文档后，逐项确认：

### requirements.md 检查清单

- [ ] 所有 FR 描述使用业务术语，无技术实现细节
- [ ] 无 API 路径、请求/响应格式
- [ ] 无数据库表名、字段类型
- [ ] 无 Prompt 模板内容
- [ ] 无具体技术名称
- [ ] 版本号已更新
- [ ] 变更记录已追加
- [ ] 文件编码为 UTF-8 BOM
- [ ] 已 push 到 GitHub

### 其他文档检查清单

- [ ] 内容未超出该文档类型的边界
- [ ] 版本号已更新
- [ ] 已 push 到 GitHub

---

## 六、当前文档清单

| 文件 | 类型 | 版本 | 状态 |
|---|---|---|---|
| design-inspiration.md | 灵感 | — | ✅ |
| requirements.md | 需求分析 | v2.5 | ✅ |
| docs-guide.md | 本文件 | v1.1 | ✅ |
| architecture.md | 概要设计 | — | ❌ 待写 |
| detailed-design.md | 详细设计 | — | ❌ 待写 |

---

*每次修改文档前，请先阅读本文档确认边界。*