"""
Discord 通知器 — 占位实现
后续接入 Discord Webhook 时完善此模块。
"""

from __future__ import annotations

import logging
from typing import Any

from .base import BaseNotifier, NotificationMessage

logger = logging.getLogger(__name__)


class DiscordNotifier(BaseNotifier):
    """Discord Webhook 推送（占位，待实现）"""

    def __init__(self, webhook_urls: list[str] | None = None):
        self.webhook_urls = webhook_urls or []

    @property
    def name(self) -> str:
        return "discord"

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> "DiscordNotifier | None":
        if not config.get("enabled", False):
            return None
        return cls(webhook_urls=config.get("webhook_urls", []))

    async def send(self, message: NotificationMessage) -> dict[str, Any]:
        """
        TODO: 调用 Discord Webhook URL 发送消息
        API: POST https://discord.com/api/webhooks/<id>/<token>
        """
        logger.warning("DiscordNotifier 尚未实现，跳过发送")
        return {
            "success": False,
            "detail": "Discord 推送尚未实现 (NotImplemented)",
            "recipient": message.recipient,
        }
