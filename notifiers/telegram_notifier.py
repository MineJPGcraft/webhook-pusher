"""
Telegram 通知器 — 基于 Telegram Bot API 的异步消息推送

API 文档: https://core.telegram.org/bots/api#sendmessage
调用方式: POST https://api.telegram.org/bot<token>/sendMessage
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from .base import BaseNotifier, NotificationMessage

logger = logging.getLogger(__name__)

# Telegram sendMessage 单条消息最大长度 4096 字符，这是规范
TELEGRAM_MSG_LIMIT = 4096

# Telegram Bot API 基础 URL，如果国内访问不了我们就去配置文件自定义代理地址
TELEGRAM_API_BASE = "https://api.telegram.org"


class TelegramNotifier(BaseNotifier):
    """Telegram Bot 推送通知器"""

    def __init__(
        self,
        bot_token: str = "",
        parse_mode: str = "HTML",
        api_base: str = TELEGRAM_API_BASE,
        timeout: float = 30.0,
    ):
        """
        Args:
            bot_token:   Telegram Bot Token (从 @BotFather 获取)
            parse_mode:  消息解析模式: "HTML" / "MarkdownV2" / "" (纯文本)
            api_base:    Telegram API 基础 URL (可自定义为反代地址)
            timeout:     HTTP 请求超时时间 (秒)
        """
        self.bot_token = bot_token
        self.parse_mode = parse_mode or None
        self.api_base = api_base.rstrip("/")
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    @property
    def name(self) -> str:
        return "telegram"

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> "TelegramNotifier | None":
        """从配置字典创建实例；若 enabled=False 或缺少 bot_token 则返回 None"""
        if not config.get("enabled", False):
            return None
        if not config.get("bot_token"):
            logger.warning("Telegram 已启用但 bot_token 为空，跳过注册")
            return None
        return cls(
            bot_token=config["bot_token"],
            parse_mode=config.get("parse_mode", "HTML"),
            api_base=config.get("api_base", TELEGRAM_API_BASE),
            timeout=config.get("timeout", 30.0),
        )

    # 内部方法

    def _get_client(self) -> httpx.AsyncClient:
        """懒加载 httpx 异步客户端（复用连接池）"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    def _build_text(self, message: NotificationMessage) -> str:
        """
        将 subject + body 组合为 Telegram 消息文本。

        当 parse_mode=HTML 时，subject 以 <b> 加粗显示；
        纯文本模式下以 "【subject】" 前缀显示。
        """
        if message.subject:
            if self.parse_mode == "HTML":
                return f"<b>{message.subject}</b>\n\n{message.body}"
            elif self.parse_mode == "MarkdownV2":
                return f"*{message.subject}*\n\n{message.body}"
            else:
                return f"【{message.subject}】\n{message.body}"
        return message.body

    def _build_payload(self, message: NotificationMessage) -> dict[str, Any]:
        """构建 Telegram API 请求体"""
        text = self._build_text(message)
        payload: dict[str, Any] = {
            "chat_id": message.recipient,
            "text": text,
        }
        if self.parse_mode:
            payload["parse_mode"] = self.parse_mode

        # 从 extra 中提取可选 Telegram 参数
        extra = message.extra
        if "disable_notification" in extra:
            payload["disable_notification"] = extra["disable_notification"]
        if "disable_web_page_preview" in extra:
            payload["disable_web_page_preview"] = extra["disable_web_page_preview"]

        return payload

    def _api_url(self, method: str) -> str:
        """构建 Telegram Bot API URL"""
        return f"{self.api_base}/bot{self.bot_token}/{method}"

    # 核心的发送实现

    async def send(self, message: NotificationMessage) -> dict[str, Any]:
        """异步发送 Telegram 消息"""
        if not self.bot_token:
            return {"success": False, "detail": "Telegram bot_token 未配置"}

        text = self._build_text(message)
        if len(text) > TELEGRAM_MSG_LIMIT:
            logger.warning(
                "消息长度 %d 超过 Telegram 限制 %d，将截断",
                len(text), TELEGRAM_MSG_LIMIT,
            )

        payload = self._build_payload(message)
        client = self._get_client()

        try:
            resp = await client.post(self._api_url("sendMessage"), json=payload)
            data = resp.json()

            if resp.status_code == 200 and data.get("ok"):
                result = data.get("result", {})
                msg_id = result.get("message_id")
                chat = result.get("chat", {})
                logger.info(
                    "Telegram 消息发送成功 -> chat_id=%s, message_id=%s",
                    message.recipient, msg_id,
                )
                return {
                    "success": True,
                    "detail": "Telegram 消息发送成功",
                    "recipient": message.recipient,
                    "message_id": msg_id,
                    "chat_info": chat,
                }
            else:
                # Telegram API 返回的错误
                error_desc = data.get("description", "未知错误")
                error_code = data.get("error_code", resp.status_code)
                logger.error(
                    "Telegram 消息发送失败 -> chat_id=%s, error_code=%s, desc=%s",
                    message.recipient, error_code, error_desc,
                )
                return {
                    "success": False,
                    "detail": f"Telegram 发送失败 [{error_code}]: {error_desc}",
                    "recipient": message.recipient,
                    "error_code": error_code,
                }

        except httpx.TimeoutException:
            logger.error("Telegram API 请求超时 (timeout=%ss)", self.timeout)
            return {
                "success": False,
                "detail": f"Telegram API 请求超时 ({self.timeout}s)",
                "recipient": message.recipient,
            }
        except httpx.ConnectError as e:
            logger.error("Telegram API 连接失败: %s", e)
            return {
                "success": False,
                "detail": f"Telegram API 连接失败: {e}",
                "recipient": message.recipient,
            }
        except Exception as e:
            logger.error("Telegram 消息发送异常: %s", e, exc_info=True)
            return {
                "success": False,
                "detail": f"Telegram 发送异常: {e}",
                "recipient": message.recipient,
            }

    async def close(self) -> None:
        """关闭 httpx 客户端连接池"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            logger.info("Telegram httpx 客户端已关闭")
