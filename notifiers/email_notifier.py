"""
邮件通知器 — 基于 aiosmtplib 的异步 SMTP 发送
"""

from __future__ import annotations

import logging
from email.message import EmailMessage
from typing import Any

import aiosmtplib

from .base import BaseNotifier, NotificationMessage

logger = logging.getLogger(__name__)


class EmailNotifier(BaseNotifier):
    """SMTP 异步邮件推送"""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int = 465,
        use_ssl: bool = True,
        use_starttls: bool = False,
        username: str = "",
        password: str = "",
        sender: str = "",
        sender_name: str = "",
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.use_ssl = use_ssl
        self.use_starttls = use_starttls
        self.username = username
        self.password = password
        self.sender = sender
        self.sender_name = sender_name

    @property
    def name(self) -> str:
        return "email"

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> "EmailNotifier | None":
        """从配置字典创建实例；若 enabled=False 则返回 None"""
        if not config.get("enabled", False):
            return None
        return cls(
            smtp_host=config["smtp_host"],
            smtp_port=config.get("smtp_port", 465),
            use_ssl=config.get("use_ssl", True),
            use_starttls=config.get("use_starttls", False),
            username=config.get("username", ""),
            password=config.get("password", ""),
            sender=config.get("sender", ""),
            sender_name=config.get("sender_name", "Webhook Pusher"),
        )

    def _build_message(self, msg: NotificationMessage) -> EmailMessage:
        """构建邮件消息对象"""
        email = EmailMessage()
        email["From"] = (
            f"{self.sender_name} <{self.sender}>" if self.sender_name else self.sender
        )
        email["To"] = msg.recipient
        email["Subject"] = msg.subject or "(无主题)"
        email.set_content(msg.body)
        return email

    async def send(self, message: NotificationMessage) -> dict[str, Any]:
        """异步发送邮件"""
        if not self.smtp_host:
            return {"success": False, "detail": "SMTP 主机未配置"}

        email_msg = self._build_message(message)

        try:
            await aiosmtplib.send(
                email_msg,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.username,
                password=self.password,
                use_tls=self.use_ssl,
                start_tls=self.use_starttls,
            )
            logger.info("邮件发送成功 -> %s", message.recipient)
            return {
                "success": True,
                "detail": "邮件发送成功",
                "recipient": message.recipient,
                "subject": message.subject,
            }
        except Exception as e:
            logger.error("邮件发送失败 -> %s: %s", message.recipient, e)
            return {
                "success": False,
                "detail": f"邮件发送失败: {e}",
                "recipient": message.recipient,
            }
