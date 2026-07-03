"""
配置加载模块
从 config.yaml 读取配置，提供全局单例访问。
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml


class ConfigError(Exception):
    """配置相关错误"""


def _find_config_file() -> Path:
    """按优先级查找配置文件"""
    # 1. 环境变量指定的路径
    env_path = os.environ.get("WEBHOOK_PUSHER_CONFIG")
    if env_path:
        p = Path(env_path)
        if p.is_file():
            return p

    # 2. 当前工作目录
    p = Path("config.yaml")
    if p.is_file():
        return p

    # 3. 项目根目录（本文件上两级）
    p = Path(__file__).resolve().parent.parent / "config.yaml"
    if p.is_file():
        return p

    raise ConfigError("找不到配置文件 config.yaml，请创建或设置环境变量 WEBHOOK_PUSHER_CONFIG")


@lru_cache(maxsize=1)
def load_config() -> dict[str, Any]:
    """加载并缓存配置文件，返回完整配置字典"""
    config_path = _find_config_file()
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if not config:
        raise ConfigError(f"配置文件 {config_path} 为空或格式错误")

    # 基本字段校验
    if "auth" not in config or "tokens" not in config["auth"]:
        raise ConfigError("配置文件缺少 auth.tokens 字段")

    return config


def get_config_section(section: str) -> dict[str, Any]:
    """获取指定配置段"""
    return load_config().get(section, {})


def reload_config() -> dict[str, Any]:
    """强制重新加载配置（清除缓存）"""
    load_config.cache_clear()
    return load_config()
