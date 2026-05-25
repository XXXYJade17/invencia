# 02 —— 认证模块详细设计

> 版本：v1.0
> 日期：2026-05-24
> 依赖：01-database.md（users 表）

---

## 一、密码哈希方案

### 1.1 算法选择

- 算法：bcrypt
- Python 库：bcrypt 4.x
- 盐轮数：12（安全与性能的平衡点）

### 1.2 实现代码

```python
import bcrypt

def hash_password(password: str) -> str:
    """对明文密码进行 bcrypt 哈希"""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(password: str, hashed: str) -> bool:
    """验证明文密码与哈希值是否匹配"""
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
```

---

## 二、JWT 方案

### 2.1 算法与库

- 算法：HS256（HMAC-SHA256）
- Python 库：PyJWT
- 密钥来源：环境变量 JWT_SECRET_KEY

### 2.2 Token 载荷结构

```json
{
  "sub": 1,
  "username": "player1",
  "iat": 1716500000,
  "exp": 1717104800
}
```

| 字段 | 含义 | 说明 |
|------|------|------|
| sub | 用户 ID | 对应 users.id |
| username | 用户名 | 便于日志/调试，不参与鉴权 |
| iat | 签发时间 | Unix 时间戳 |
| exp | 过期时间 | iat + 604800（7天） |

### 2.3 核心实现

```python
import jwt
import time
import os

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
TOKEN_EXPIRE_SECONDS = 7 * 24 * 3600  # 7 天
REFRESH_WINDOW_SECONDS = 24 * 3600     # 24 小时续期窗口

def create_token(user_id: int, username: str) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "username": username,
        "iat": now,
        "exp": now + TOKEN_EXPIRE_SECONDS
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_token(token: str) -> dict:
    """验证 Token，返回载荷；过期或无效则抛出异常"""
    return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

def should_refresh(payload: dict) -> bool:
    """判断是否在续期窗口内"""
    now = int(time.time())
    return payload["exp"] - now < REFRESH_WINDOW_SECONDS
```

---

## 三、FastAPI 认证中间件

### 3.1 依赖注入函数

```python
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer(auto_error=False)

async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security)
) -> dict:
    """从请求中提取并验证当前用户信息"""
    if not credentials:
        raise HTTPException(status_code=401, detail="未提供认证凭证")

    try:
        payload = verify_token(credentials.credentials)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="凭证已过期")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="凭证无效")

    return {"user_id": payload["sub"], "username": payload["username"]}
```

### 3.2 Token 续期中间件

> 在认证成功后、返回响应前，检查是否需要刷新 Token。新 Token 通过响应头 X-New-Token 返回。

```python
from starlette.middleware.base import BaseHTTPMiddleware

class TokenRefreshMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                payload = verify_token(token)
                if should_refresh(payload):
                    new_token = create_token(
                        payload["sub"], payload["username"]
                    )
                    response.headers["X-New-Token"] = new_token
            except Exception:
                pass

        return response
```

---

## 四、注册/登录服务实现

### 4.1 注册

```python
def register_user(username: str, password: str) -> dict:
    """注册新用户，返回用户信息 + Token"""
    # 1. 校验用户名格式
    if not (2 <= len(username) <= 20):
        raise ValueError("用户名长度需在 2-20 字符之间")
    if not re.match(r"^[一-龥a-zA-Z0-9_]+$", username):
        raise ValueError("用户名仅允许中文、英文、数字、下划线")

    # 2. 校验密码长度
    if not (6 <= len(password) <= 32):
        raise ValueError("密码长度需在 6-32 字符之间")

    # 3. 检查用户名唯一性
    with get_db() as conn:
        existing = conn.execute(
            "SELECT id FROM users WHERE username = ? AND del_flag = 0",
            (username,)
        ).fetchone()
        if existing:
            raise ValueError("用户名已存在")

        # 4. 创建用户
        password_hash = hash_password(password)
        cursor = conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash)
        )
        user_id = cursor.lastrowid

    # 5. 签发 Token
    token = create_token(user_id, username)
    return {"token": token, "user": {"id": user_id, "username": username}}
```

### 4.2 登录

```python
def login_user(username: str, password: str) -> dict:
    """验证用户登录，返回用户信息 + Token"""
    with get_db() as conn:
        user = conn.execute(
            "SELECT id, username, password_hash FROM users WHERE username = ? AND del_flag = 0",
            (username,)
        ).fetchone()

        if not user:
            raise ValueError("用户名或密码错误")

        if not verify_password(password, user["password_hash"]):
            raise ValueError("用户名或密码错误")

    token = create_token(user["id"], user["username"])
    return {"token": token, "user": {"id": user["id"], "username": user["username"]}}
```

### 4.3 Token 刷新（手动）

```python
def refresh_token(user_id: int, username: str) -> str:
    """手动刷新 Token（POST /api/auth/refresh）"""
    return create_token(user_id, username)
```

---

## 五、前端认证实现

### 5.1 Token 存储

```javascript
// auth.js
const AUTH_KEY = "invencia_token";

export function getToken() {
  return localStorage.getItem(AUTH_KEY);
}

export function setToken(token) {
  localStorage.setItem(AUTH_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(AUTH_KEY);
}

export function isLoggedIn() {
  return !!getToken();
}
```

### 5.2 API 请求拦截

```javascript
// api.js
export async function apiFetch(url, options = {}) {
  const token = getToken();
  const headers = {
    "Content-Type": "application/json",
    ...(token && { Authorization: Bearer  }),
    ...options.headers
  };

  const response = await fetch(url, { ...options, headers });

  // Token 续期：检查响应头
  const newToken = response.headers.get("X-New-Token");
  if (newToken) setToken(newToken);

  // 401 处理
  if (response.status === 401) {
    clearToken();
    window.location.hash = "#/";
    showLoginModal();
    return null;
  }

  return response.json();
}
```

### 5.3 路由守卫

```javascript
// router.js
const PUBLIC_ROUTES = ["#/", "#/login"];

function handleRoute() {
  const hash = window.location.hash || "#/";

  if (!PUBLIC_ROUTES.includes(hash) && !isLoggedIn()) {
    window.location.hash = "#/";
    showLoginModal();
    return;
  }

  // 渲染对应页面...
}

window.addEventListener("hashchange", handleRoute);
window.addEventListener("load", handleRoute);
```

---

*02-auth.md v1.0 完成。下一步：[03-characters.md](./03-characters.md)。*

