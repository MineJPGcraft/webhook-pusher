"""
Notifier 抽象基类
所有推送渠道（邮件、Telegram、Discord 等）均继承此类，
实现 send 方法即可被注册到推送调度器中。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class NotificationMessage:
    """统一的推送消息模型"""

    recipient: str                        # 收件人/目标 (邮箱地址、chat_id、webhook URL 等)
    subject: str = ""                     # 标题 (邮件主题、消息标题等)
    body: str = ""                        # 正文内容
    extra: dict[str, Any] = field(default_factory=dict)  # 渠道特有参数


class BaseNotifier(ABC):
    """
    推送通知器抽象基类。

    子类需实现:
        - name: 渠道名称 (如 "email", "telegram", "discord")
        - send(): 异步发送方法
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """渠道唯一标识，如 'email', 'telegram', 'discord'"""
        ...

    @abstractmethod
    async def send(self, message: NotificationMessage) -> dict[str, Any]:
        """
        异步发送推送消息。

        Args:
            message: 统一消息模型

        Returns:
            包含发送结果的字典，至少包含:
            {
                "success": bool,
                "detail": str,
                ...
            }
        """
        ...

    async def close(self) -> None:
        """清理资源（如关闭连接），子类按需实现"""
        pass
