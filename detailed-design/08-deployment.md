# 08 —— 部署详细设计

> 版本：v1.0
> 日期：2026-05-24
> 依赖：architecture.md 九

---

## 一、环境变量清单

### 1.1 必需变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| JWT_SECRET_KEY | JWT 签名密钥 | openssl rand -hex 32 生成 |
| Dify_API_KEY | Dify API 密钥 | pat_xxxx |
| Dify_API_BASE | Dify API 地址 | https://api.Dify.cn |
| Dify_WF_CHAR_CREATE | 角色创建工作流 ID | 7389xxxx |
| Dify_WF_NARRATIVE | 天道推演工作流 ID | 7390xxxx |

### 1.2 可选变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| DB_PATH | 数据库文件路径 | data/invencia.db |
| UVICORN_HOST | 监听地址 | 127.0.0.1 |
| UVICORN_PORT | 监听端口 | 8000 |
| LOG_LEVEL | 日志级别 | info |
| CORS_ORIGINS | 允许的跨域来源 | * |

### 1.3 .env 示例

```
# Invencia 环境配置
JWT_SECRET_KEY=a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6
Dify_API_KEY=pat_xxxxxxxxxxxxxxxxxxxxxxxxx
Dify_API_BASE=https://api.Dify.cn
Dify_WF_CHAR_CREATE=7389123456789012345
Dify_WF_NARRATIVE=7390123456789012346
DB_PATH=data/invencia.db
UVICORN_HOST=127.0.0.1
UVICORN_PORT=8000
LOG_LEVEL=info
```

---

## 二、Nginx 配置

```nginx
server {
    listen 80;
    server_name invencia.example.com;

    # 静态资源（前端文件）
    root /opt/invencia/frontend;
    index index.html;

    # gzip 压缩
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml;
    gzip_min_length 256;

    # SPA：所有非 /api/ 路径回退到 index.html
    location / {
        try_files  / /index.html;
    }

    # API 反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host System.Management.Automation.Internal.Host.InternalHost;
        proxy_set_header X-Real-IP ;
        proxy_set_header X-Forwarded-For ;
        proxy_set_header X-Forwarded-Proto ;

        # 超时（AI API 调用可能需要较长时间）
        proxy_read_timeout 35s;
        proxy_connect_timeout 5s;
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

---

## 三、Uvicorn 启动配置

### 3.1 命令行启动

```bash
# 开发环境
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

# 生产环境（systemd）
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --workers 1 --log-level info
```

### 3.2 Systemd 服务

```ini
# /etc/systemd/system/invencia.service
[Unit]
Description=Invencia Backend
After=network.target

[Service]
Type=simple
User=invencia
WorkingDirectory=/opt/invencia
EnvironmentFile=/opt/invencia/.env
ExecStart=/opt/invencia/venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000 --workers 1
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
```

---

## 四、部署步骤

### 4.1 首次部署

```bash
# 1. 创建部署目录
mkdir -p /opt/invencia/{frontend,backend,data}

# 2. 克隆代码
cd /opt/invencia
git clone git@github.com:XXXYJade17/invencia.git .

# 3. 创建 Python 虚拟环境
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env，填入密钥和 Dify 工作流 ID

# 5. 初始化数据库
python -c "from backend.db.migrations import init_db; init_db()"

# 6. 配置 Nginx
cp deploy/nginx.conf /etc/nginx/sites-available/invencia
ln -s /etc/nginx/sites-available/invencia /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

# 7. 启动服务
systemctl enable --now invencia.service

# 8. 验证
curl http://localhost:8000/api/worlds
```

### 4.2 Python 依赖（requirements.txt）

```
fastapi>=0.110,<1.0
uvicorn[standard]>=0.29,<1.0
pydantic>=2.0,<3.0
pyjwt>=2.8,<3.0
bcrypt>=4.1,<5.0
httpx>=0.27,<1.0
python-dotenv>=1.0,<2.0
```

---

## 五、数据库备份

- SQLite 单文件，备份只需复制
- 建议设置 cron 定时备份：

```bash
# 每天凌晨 3 点备份
0 3 * * * cp /opt/invencia/data/invencia.db /opt/invencia/data/backup/invencia_.db
# 保留最近 7 天的备份
0 4 * * * find /opt/invencia/data/backup/ -name "*.db" -mtime +7 -delete
```

---

*08-deployment.md v1.0 完成。详细设计全部完成。*

