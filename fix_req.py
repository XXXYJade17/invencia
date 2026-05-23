# -*- coding: utf-8 -*-
import sys

with open(r"D:\Project\docs\invencia\requirements.md", "r", encoding="utf-8-sig", newline="") as f:
    content = f.read()

NL = "\r\n"

# 1. FR-CHAR-001 -> modal version
content = content.replace(
    "#### FR-CHAR-001 角色列表" + NL + "- **规则**：登录后展示当前用户的所有角色（MVP 阶段限制每个用户最多 1 个角色）" + NL + "- **展示**：角色名、性别、境界简述、最后游玩时间",
    "#### FR-CHAR-001 角色列表弹窗" + NL + "- **触发**：登录后自动弹出；也可从游戏界面导航栏入口打开" + NL + "- **展示**：已创建的角色列表，每项显示角色名、性别、境界简述、最后游玩时间" + NL + "- **操作**：点击角色 → 进入游戏；点击" + '"创建新角色"' + " → 弹出创建角色弹窗" + NL + "- **空状态**：无角色时列表为空，仅显示" + '"创建新角色"' + "按钮和引导文案"
)

# 2. Remove FR-GAME-008
content = content.replace(
    "#### FR-GAME-008 新对话开始" + NL + "- **规则**：玩家可开始" + '"新的一天"' + "（新 session），切换后不可返回之前的会话" + NL + "- **实现**：创建新的 conversation_id，从 infomation 当前状态继续" + NL + NL,
    ""
)

# 3. Add FR-CHAR-005 after FR-CHAR-004 section
fr_char_005 = NL + "#### FR-CHAR-005 按世界查询角色列表" + NL + "- **描述**：根据世界 ID 查询当前用户在该世界下的所有角色" + NL + "- **输入**：`world_id`（可选，不传则返回全部世界的角色）" + NL + "- **规则**：与 FR-CHAR-001 共用同一接口 `GET /api/characters`，通过 query 参数区分" + NL + "- **输出**：角色简要列表（id、name、gender、realm_summary、updated_at）" + NL + "- **使用场景**：角色列表弹窗按世界分类展示" + NL
content = content.replace(
    "#### FR-CHAR-004 角色面板实时更新" + NL + "- **规则**：每次 `/game/act` 返回后，前端获取最新的 infomation 并在面板中刷新" + NL + NL + "---",
    "#### FR-CHAR-004 角色面板实时更新" + NL + "- **规则**：每次 `/game/act` 返回后，前端获取最新的 infomation 并在面板中刷新" + NL + fr_char_005 + NL + "---"
)

# 4. Fix auth redirects
content = content.replace("跳转角色列表页", "弹出角色列表弹窗")

# 5. Fix version
content = content.replace("版本：v1.4", "版本：v1.5")
content = content.replace(
    "> - v1.4：新增文档边界说明，明确需求分析与其他设计文档的分工",
    "> - v1.5：完善 FR-CHAR-001 角色列表弹窗、移除 FR-GAME-008、新增 FR-CHAR-005" + NL + "> - v1.4：新增文档边界说明，明确需求分析与其他设计文档的分工"
)
content = content.replace("*需求分析 v1.4 完成", "*需求分析 v1.5 完成")

with open(r"D:\Project\docs\invencia\requirements.md", "w", encoding="utf-8-sig", newline="") as f:
    f.write(content)

# Verify
with open(r"D:\Project\docs\invencia\requirements.md", "rb") as f:
    raw = f.read()

checks = [
    ("FR-GAME-008 gone", b"FR-GAME-008" not in raw),
    ("FR-CHAR-005 exists", b"FR-CHAR-005" in raw),
    ("v1.5", b"v1.5" in raw),
    ("No corruption", raw.count(b"?") < 5),
]
for name, ok in checks:
    print(f"{'OK' if ok else 'FAIL'} {name}")

# Quick sanity: count FRs
count = 0
for b in range(len(raw)):
    if raw[b:b+3] == b"FR-":
        count += 1
print(f"FR occurrences: {count}")
