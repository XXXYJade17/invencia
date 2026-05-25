# 01 —— 数据库详细设计

> 版本：v1.0
> 日期：2026-05-24
> 依赖：architecture.md 六

---

## 一、数据库引擎与配置

### 1.1 引擎选择

- 数据库：SQLite 3
- 驱动：Python sqlite3 标准库
- 文件路径：data/invencia.db

### 1.2 WAL 模式配置

```sql
-- 连接后立即执行
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA foreign_keys=ON;
PRAGMA busy_timeout=5000;
```

| 参数 | 值 | 说明 |
|------|-----|------|
| journal_mode | WAL | 写前日志，允许多读一写，提升并发 |
| synchronous | NORMAL | 平衡安全性（默认 FULL 太慢） |
| foreign_keys | ON | 启用外键约束 |
| busy_timeout | 5000ms | 写冲突时等待 5 秒而非立即报错 |

### 1.3 连接管理

```python
import sqlite3
from contextlib import contextmanager

DB_PATH = "data/invencia.db"

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
```

---

## 二、建表 DDL

### 2.1 用户表（users）

```sql
CREATE TABLE IF NOT EXISTS users (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    username   TEXT    NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    del_flag   INTEGER NOT NULL DEFAULT 0
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username
    ON users(username)
    WHERE del_flag = 0;
```

### 2.2 世界配置表（world_config）

```sql
CREATE TABLE IF NOT EXISTS world_config (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT    NOT NULL,
    display_name  TEXT    NOT NULL,
    description   TEXT    NOT NULL,
    system_prompt TEXT    NOT NULL,
    cover_image   TEXT,
    tags          TEXT,
    sort_order    INTEGER NOT NULL DEFAULT 0,
    is_active     INTEGER NOT NULL DEFAULT 1,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at    TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_world_config_active
    ON world_config(sort_order, is_active);
```

### 2.3 角色表（characters）

```sql
CREATE TABLE IF NOT EXISTS characters (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id),
    world_id   INTEGER NOT NULL REFERENCES world_config(id),
    name       TEXT    NOT NULL,
    gender     TEXT    NOT NULL,
    infomation TEXT    NOT NULL,
    is_dead    INTEGER NOT NULL DEFAULT 0,
    created_at TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    del_flag   INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_characters_user
    ON characters(user_id, del_flag);

CREATE INDEX IF NOT EXISTS idx_characters_world
    ON characters(world_id, user_id)
    WHERE del_flag = 0;
```

### 2.4 消息表（messages）

```sql
CREATE TABLE IF NOT EXISTS messages (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id  INTEGER NOT NULL REFERENCES characters(id),
    role          TEXT    NOT NULL,
    content       TEXT    NOT NULL,
    metadata      TEXT,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    del_flag      INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_messages_character_time
    ON messages(character_id, created_at DESC)
    WHERE del_flag = 0;

CREATE INDEX IF NOT EXISTS idx_messages_character_id
    ON messages(character_id, id)
    WHERE del_flag = 0;
```

---

## 三、索引汇总

| # | 表 | 索引名 | 字段 | 类型 | 用途 |
|---|------|--------|------|------|------|
| 1 | users | idx_users_username | username | UNIQUE, Partial | 登录查重 |
| 2 | world_config | idx_world_config_active | sort_order, is_active | Composite | 世界列表排序 |
| 3 | characters | idx_characters_user | user_id, del_flag | Composite | 用户角色列表 |
| 4 | characters | idx_characters_world | world_id, user_id | Composite, Partial | 按世界过滤 |
| 5 | messages | idx_messages_character_time | character_id, created_at DESC | Composite, Partial | 时间序历史 |
| 6 | messages | idx_messages_character_id | character_id, id | Composite, Partial | 分页游标 |

> Partial Index：WHERE del_flag = 0，索引仅覆盖未删除记录，减小索引体积。

---

## 四、迁移策略

### 4.1 初始化脚本

```python
def init_db():
    """首次部署时调用，幂等（IF NOT EXISTS）"""
    with get_db() as conn:
        conn.executescript('''
        CREATE TABLE IF NOT EXISTS users (...);
        CREATE TABLE IF NOT EXISTS world_config (...);
        CREATE TABLE IF NOT EXISTS characters (...);
        CREATE TABLE IF NOT EXISTS messages (...);
        -- 插入默认修仙世界配置
        INSERT OR IGNORE INTO world_config (name, display_name, ...)
        VALUES ('cultivation', '玄天界', ...);
        ''')
```

### 4.2 版本迁移

- 使用 user_version PRAGMA 追踪 schema 版本
- 启动时检查 PRAGMA user_version，按需执行增量迁移 SQL

```python
def migrate_db():
    with get_db() as conn:
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        if version < 1:
            # v1: 初始 schema
            init_db()
            conn.execute("PRAGMA user_version = 1")
        # if version < 2: ...
```

### 4.3 种子数据：默认修仙世界

```sql
INSERT OR IGNORE INTO world_config
    (name, display_name, description, system_prompt, tags, sort_order, is_active)
VALUES
    ('cultivation',
     '玄天界',
     '一个名为"五域"的修仙世界，包含苍玄、焚天、无尘、玄冥、混元五块大陆...',
     '[见 05-Dify-workflows.md 天道 System Prompt]',
     '["修仙", "东方玄幻", "叙事RPG"]',
     1,
     1);
```

---

## 五、软删除规范

- 所有查询必须加 WHERE del_flag = 0（除登录需查所有用户校验用户名唯一性）
- 删除操作一律用 UPDATE SET del_flag = 1，禁止物理 DELETE
- 用户名唯一性约束通过 Partial Unique Index 实现，del_flag=1 的用户名可被复用

---

*01-database.md v1.0 完成。下一步：[02-auth.md](./02-auth.md)。*

