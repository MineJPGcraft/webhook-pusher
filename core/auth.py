"""
认证中间件
"""

from __future__ import annotations

import secrets

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import load_config

# Bearer token 提取器
bearer_scheme = HTTPBearer(auto_error=False)


async def verify_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    """
    验证 Bearer Token。
    依赖注入用法: `token: str = Depends(verify_token)`

    成功返回 token 字符串，失败抛出 401。
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少认证信息，请在 Authorization 头中提供 Bearer Token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    config = load_config()
    valid_tokens: list[str] = config.get("auth", {}).get("tokens", [])

    # 使用 secrets.compare_digest 防止时序攻击 那真是太猎奇了
    token = credentials.credentials
    is_valid = any(secrets.compare_digest(token, t) for t in valid_tokens)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的 Token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token
