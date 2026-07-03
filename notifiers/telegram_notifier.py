"""
Telegram 通知器 — 占位实现
后续接入 Telegram Bot API 时完善此模块。
"""

from __future__ import annotations

import logging
from typing import Any

from .base import BaseNotifier, NotificationMessage

logger = logging.getLogger(__name__)


class TelegramNotifier(BaseNotifier):
    """Telegram Bot 推送（占位，待实现）"""

    def __init__(self, bot_token: str = ""):
        self.bot_token = bot_token

    @property
    def name(self) -> str:
        return "telegram"

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> "TelegramNotifier | None":
        if not config.get("enabled", False):
            return None
        return cls(bot_token=config.get("bot_token", ""))

    async def send(self, message: NotificationMessage) -> dict[str, Any]:
        """
        TODO: 调用 Telegram Bot API 发送消息
        API: https://api.telegram.org/bot<token>/sendMessage
        """
        logger.warning("TelegramNotifier 尚未实现，跳过发送")
        return {
            "success": False,
            "detail": "Telegram 推送尚未实现 (NotImplemented)",
            "recipient": message.recipient,
        }
