# -*- coding: utf-8 -*-
"""Cookie 字符串解析模块"""

from __future__ import annotations

from typing import Dict, Optional

from ..patterns import COOKIE_AUTH_TOKEN_RE, COOKIE_CT0_RE


def parse_cookie_string(cookie_str: str) -> Optional[Dict[str, str]]:
    """从浏览器 Cookie 字符串中提取 auth_token 和 ct0

    支持从浏览器开发者工具复制的完整 Cookie 字符串中提取关键认证信息。

    Args:
        cookie_str: Cookie 字符串，格式如 "auth_token=xxx; ct0=yyy; ..."

    Returns:
        包含 auth_token 和 ct0 的字典，如果提取失败则返回 None

    Examples:
        >>> parse_cookie_string("auth_token=abc123def456; ct0=789xyz012; lang=en")
        {'auth_token': 'abc123def456', 'ct0': '789xyz012'}

        >>> parse_cookie_string("invalid cookie") is None
        True
    """
    from tmdc.constants import C

    if not cookie_str or len(cookie_str) < C.COOKIE_MIN_LEN:
        return None

    auth_match = COOKIE_AUTH_TOKEN_RE.search(cookie_str)
    ct0_match = COOKIE_CT0_RE.search(cookie_str)

    if auth_match and ct0_match:
        return {"auth_token": auth_match.group(1), "ct0": ct0_match.group(1)}
    return None


__all__ = ["parse_cookie_string"]
