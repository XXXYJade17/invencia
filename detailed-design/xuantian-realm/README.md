# 玄天界 —— 设定与提示词

> Invencia MVP 首个世界。本目录包含玄天界的完整世界观设定、角色模板、AI 提示词和工具设计。

---

## 文件索引

| # | 文件 | 内容 |
|---|------|------|
| 1 | [01-setting.md](./01-setting.md) → [setting/](./setting/) | 世界设定索引（5文件：简介/五域/历史/修炼路径/规则） |
| 2 | [02-char-template.md](./02-char-template.md) | 角色信息 JSON 模板：字段定义、凡人模板、合并规则 |
| 3 | [03-prompts.md](./03-prompts.md) | AI Prompt 合集：角色创建 Prompt + 天道推演 Agent Prompt |
| 4 | [04-tools.md](./04-tools.md) | 工具设计：道韵评定器 + 未来工具模板 |

---

## 阅读顺序

```
01-setting.md           ← 先理解世界
  └── 02-char-template.md  ← 再理解角色数据结构
        ├── 03-prompts.md   ← 理解 AI 如何使用数据和规则
        └── 04-tools.md     ← 理解辅助工具
```

---

## 与外部文件的关系

| 外部文件 | 关系 |
|----------|------|
| `../03-characters.md` | 引用本目录的角色模板 |
| `../04-game-engine.md` | 引用本目录的 Prompt 和工具 |
| `../05-dify-workflows.md` | 引用本目录的 Prompt 配置 |
| `../../design-inspiration.md` | 玄天界内容已迁移至此，原文档指向此处 |

---

*玄天界设定 v1.0。所有关于玄天界的设定和提示词集中于此。*
