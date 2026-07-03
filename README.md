# Webhook Pusher

通用 Webhook 消息推送服务 — 通过 HTTP Webhook 调用发送邮件（SMTP），预留 Telegram / Discord 等渠道扩展接口。

## ✨ 功能特性

- **邮件推送**：基于 SMTP 异步发送（aiosmtplib），支持 SSL / STARTTLS
- **身份验证**：Bearer Token 认证，防止接口被滥用
- **多渠道架构**：抽象 Notifier 基类，插件式注册新渠道
- **配置驱动**：YAML 配置文件，修改无需改代码
- **转义符换行**：正文中 `\n` 自动转换为真实换行

## 📁 项目结构

```
webhook-pusher/
├── main.py                     # 服务入口
├── config.yaml                 # 配置文件 (SMTP、Token、各渠道开关)
├── requirements.txt            # Python 依赖
├── core/
│   ├── __init__.py
│   ├── config.py               # 配置加载器
│   ├── auth.py                 # Bearer Token 认证中间件
│   └── server.py               # FastAPI 应用与路由
└── notifiers/
    ├── __init__.py
    ├── base.py                 # Notifier 抽象基类 + 统一消息模型
    ├── email_notifier.py       # SMTP 邮件通知器
    ├── telegram_notifier.py    # Telegram 通知器 (占位)
    └── discord_notifier.py     # Discord 通知器 (占位)
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 编辑配置

编辑 `config.yaml`，填写你的 SMTP 信息和认证 Token：

```yaml
auth:
  tokens:
    - "your-secret-token-here"

email:
  enabled: true
  smtp_host: "smtp.gmail.com"
  smtp_port: 465
  use_ssl: true
  username: "you@gmail.com"
  password: "your-app-password"   # Gmail 需使用应用专用密码
  sender: "you@gmail.com"
  sender_name: "Webhook Pusher"
```

### 3. 启动服务

```bash
python main.py
```

服务默认运行在 `http://0.0.0.0:8000`。

### 4. 调用 Webhook

#### 发送邮件（快捷接口）

```bash
curl -X POST http://localhost:8000/push/email \
  -H "Authorization: Bearer your-secret-token-here" \
  -H "Content-Type: application/json" \
  -d '{
    "recipient": "to@example.com",
    "subject": "测试邮件",
    "body": "你好！\n这是第二行内容。"
  }'
```

#### 通用推送接口（指定渠道）

```bash
curl -X POST http://localhost:8000/push \
  -H "Authorization: Bearer your-secret-token-here" \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "email",
    "recipient": "to@example.com",
    "subject": "测试邮件",
    "body": "正文内容\\n换行测试"
  }'
```

#### 查看可用渠道

```bash
curl http://localhost:8000/channels \
  -H "Authorization: Bearer your-secret-token-here"
```

#### 健康检查（无需认证）

```bash
curl http://localhost:8000/health
```

## 📡 API 接口说明

| 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|
| `GET` | `/health` | ❌ | 健康检查，返回可用渠道列表 |
| `GET` | `/channels` | ✅ | 查看当前启用的推送渠道 |
| `POST` | `/push` | ✅ | 通用推送，通过 `channel` 字段指定渠道 |
| `POST` | `/push/email` | ✅ | 快捷邮件推送 |

### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `channel` | string | `/push` 必填 | 推送渠道：`email` / `telegram` / `discord` |
| `recipient` | string | ✅ | 收件人邮箱地址 / chat_id / webhook URL |
| `subject` | string | ❌ | 标题（邮件主题等） |
| `body` | string | ✅ | 正文，`\n` 会被自动转为换行 |

### 认证方式

所有需认证的接口要求在请求头中携带：

```
Authorization: Bearer <your-token>
```

Token 在 `config.yaml` → `auth.tokens` 中配置，支持多个 Token。

## 🔧 扩展新渠道

1. 在 `notifiers/` 下新建文件，继承 `BaseNotifier`：

```python
from .base import BaseNotifier, NotificationMessage

class MyNotifier(BaseNotifier):
    @property
    def name(self) -> str:
        return "my_channel"

    async def send(self, message: NotificationMessage) -> dict:
        # 实现发送逻辑
        return {"success": True, "detail": "发送成功"}
```

2. 在 `config.yaml` 中添加对应配置段。

3. 在 `core/server.py` 的 `init_notifiers()` 中注册：

```python
from notifiers.my_notifier import MyNotifier
my_notifier = MyNotifier.from_config(config.get("my_channel", {}))
if my_notifier:
    registry.register(my_notifier)
```

4. 调用时指定 `channel: "my_channel"` 即可。

## 📝 常见 SMTP 配置参考

| 服务商 | smtp_host | smtp_port | use_ssl | use_starttls |
|--------|-----------|-----------|---------|-------------|
| Gmail | smtp.gmail.com | 465 | true | false |
| Gmail (STARTTLS) | smtp.gmail.com | 587 | false | true |
| QQ 邮箱 | smtp.qq.com | 465 | true | false |
| 163 邮箱 | smtp.163.com | 465 | true | false |
| Outlook | smtp-mail.outlook.com | 587 | false | true |

> **注意**：Gmail、QQ 等邮箱需使用「应用专用密码」而非登录密码。

## 📄 License

MIT
