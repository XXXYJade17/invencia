# 玄天界 —— Prompt 合集

> 版本：v2.0
> 日期：2026-05-27

Prompt 全文已提取为独立文件：

| 文件 | 用途 | Dify 资源 |
|------|------|-----------|
| [prompts/char-create.md](char-create_system_prompt.md) | 角色创建 | Workflow `char-creation` → LLM 节点 |
| [prompts/narrative.md](./prompts/narrative.md) | 天道推演 | Chatflow `tiandao-narrative` → Agent 节点 |

### 运行时文件

```
backend/prompts/
├── char_create.txt         角色创建 System Prompt
└── narrative.txt           天道推演 Agent System Prompt
```

后端启动时读取 `.txt` → Dify API `inputs.system_prompt` 传入。

---

*玄天界 Prompt 合集索引。详细 Prompt 全文见 prompts/ 子目录。*
