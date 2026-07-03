"""
FastAPI的应用与服务路由
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import Depends, FastAPI
from pydantic import BaseModel, Field

from core.auth import verify_token
from core.config import get_config_section, load_config
from notifiers.base import BaseNotifier, NotificationMessage
from notifiers.email_notifier import EmailNotifier
from notifiers.telegram_notifier import TelegramNotifier
from notifiers.discord_notifier import DiscordNotifier

logger = logging.getLogger(__name__)

#  在这里请求/响应


class PushRequest(BaseModel):
    """通用推送请求"""

    channel: str = Field("email", description="推送渠道: email / telegram / discord")
    recipient: str = Field(..., description="收件人/目标地址")
    subject: str = Field("", description="标题 (邮件主题、消息标题等)")
    body: str = Field(..., description="正文内容，支持 \\n 换行")


class EmailPushRequest(BaseModel):
    """快捷邮件推送请求 (无需指定 channel)"""

    recipient: str = Field(..., description="收件人邮箱地址")
    subject: str = Field("", description="邮件主题")
    body: str = Field(..., description="邮件正文，支持 \\n 换行")


class PushResponse(BaseModel):
    """推送响应"""

    success: bool
    channel: str
    detail: str
    results: list[dict[str, Any]] = Field(default_factory=list)


#  Notifier 注册表 — 插件式管理 以后还要扩展很多平台


class NotifierRegistry:
    """通知器注册表，管理所有已启用的推送渠道"""

    def __init__(self):
        self._notifiers: dict[str, BaseNotifier] = {}

    def register(self, notifier: BaseNotifier) -> None:
        self._notifiers[notifier.name] = notifier
        logger.info("已注册通知器: %s", notifier.name)

    def get(self, channel: str) -> BaseNotifier | None:
        return self._notifiers.get(channel)

    def list_channels(self) -> list[str]:
        return list(self._notifiers.keys())

    async def close_all(self) -> None:
        for notifier in self._notifiers.values():
            await notifier.close()


#  全局注册表初始化

registry = NotifierRegistry()


def init_notifiers() -> None:
    """根据配置文件初始化所有通知器"""
    config = load_config()

    email_notifier = EmailNotifier.from_config(config.get("email", {}))
    if email_notifier:
        registry.register(email_notifier)

    telegram_notifier = TelegramNotifier.from_config(config.get("telegram", {}))
    if telegram_notifier:
        registry.register(telegram_notifier)

    discord_notifier = DiscordNotifier.from_config(config.get("discord", {}))
    if discord_notifier:
        registry.register(discord_notifier)


#  声明 FastAPI 应用

app = FastAPI(
    title="Webhook Pusher",
    description="通用 Webhook 消息推送服务 — 支持邮件、Telegram、Discord 等多渠道",
    version="1.0.0",
)


@app.on_event("startup")
async def _startup():
    init_notifiers()
    logger.info("可用推送渠道: %s", registry.list_channels())


@app.on_event("shutdown")
async def _shutdown():
    await registry.close_all()


#  路由


@app.get("/health")
async def health_check():
    """健康检查（无需认证）"""
    return {"status": "ok", "channels": registry.list_channels()}


@app.get("/channels")
async def list_channels(token: str = Depends(verify_token)):
    """查看当前可用的推送渠道"""
    return {"channels": registry.list_channels()}


@app.post("/push", response_model=PushResponse)
async def push(req: PushRequest, token: str = Depends(verify_token)):
    """
    通用推送接口 — 根据 channel 字段路由到对应通知器。

    支持的 channel: email, telegram, discord
    """
    notifier = registry.get(req.channel)
    if notifier is None:
        return PushResponse(
            success=False,
            channel=req.channel,
            detail=f"不支持的推送渠道: {req.channel}，可用: {registry.list_channels()}",
        )

    # 处理转义符换行: 将字面量 \n 转为实际换行
    body = req.body.replace("\\n", "\n")

    message = NotificationMessage(
        recipient=req.recipient,
        subject=req.subject,
        body=body,
    )

    result = await notifier.send(message)
    return PushResponse(
        success=result.get("success", False),
        channel=req.channel,
        detail=result.get("detail", ""),
        results=[result],
    )


@app.post("/push/email", response_model=PushResponse)
async def push_email(req: EmailPushRequest, token: str = Depends(verify_token)):
    """
    快捷邮件推送接口 — 无需指定 channel，直接发送邮件。 懒人必备！

    请求体:
        {
            "recipient": "to@example.com",
            "subject": "邮件标题",
            "body": "邮件正文\\n第二行"
        }
    """
    notifier = registry.get("email")
    if notifier is None:
        return PushResponse(
            success=False,
            channel="email",
            detail="邮件推送未启用，请在 config.yaml 中配置 email.enabled=true",
        )

    body = req.body.replace("\\n", "\n")

    message = NotificationMessage(
        recipient=req.recipient,
        subject=req.subject,
        body=body,
    )

    result = await notifier.send(message)
    return PushResponse(
        success=result.get("success", False),
        channel="email",
        detail=result.get("detail", ""),
        results=[result],
    )
