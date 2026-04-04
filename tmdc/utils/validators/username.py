# -*- coding: utf-8 -*-
"""用户名验证和处理模块"""

from __future__ import annotations

import re
from typing import Union

from ...constants import C
from ..patterns import USERNAME_RE


def validate_username(username: str) -> tuple[bool, str]:
    """验证 Twitter 用户名格式

    Twitter 用户名规则：
    - 长度：1-15 个字符
    - 只能包含字母、数字、下划线

    Args:
        username: 需要验证的用户名

    Returns:
        Tuple[bool, str]: (是否有效, 错误信息)

    Examples:
        >>> validate_username("elonmusk")
        (True, '')
        >>> validate_username("a" * 16)
        (False, '用户名长度超出限制（最多15个字符）')
        >>> validate_username("invalid-user")
        (False, '用户名只能包含字母、数字和下划线')
    """
    if not username:
        return False, "用户名不能为空"

    username = username.lstrip("@")

    if not username:
        return False, "用户名不能为空"

    if len(username) > 15:
        return False, "用户名长度超出限制（最多15个字符）"

    if not USERNAME_RE.match(username):
        return False, "用户名只能包含字母、数字和下划线"

    return True, ""


def clean_username(raw: str) -> Union[str, None]:
    """清理用户名（移除@前缀、URL、括号格式）

    支持的输入格式：
    - @username
    - https://x.com/username
    - https://twitter.com/username
    - Name(username)
    - username

    Args:
        raw: 原始输入字符串

    Returns:
        清理后的用户名，如果无效返回 None

    Examples:
        >>> clean_username("@elonmusk")
        'elonmusk'
        >>> clean_username("https://x.com/elonmusk")
        'elonmusk'
        >>> clean_username("Elon Musk(elonmusk)")
        'elonmusk'
        >>> clean_username("invalid user!")
        None
    """
    if not raw:
        return None

    raw = raw.strip()

    url_match = re.match(r"https?://(?:x|twitter)\.com/([^/?]+)", raw, re.IGNORECASE)
    if url_match:
        return url_match.group(1).lower()

    bracket_match = re.match(r".+\(([^)]+)\)$", raw)
    if bracket_match:
        candidate = bracket_match.group(1).strip()
        if re.match(r"^[a-zA-Z0-9_]{1,15}$", candidate):
            return candidate.lower()

    if raw.startswith("@"):
        raw = raw[1:]

    if re.match(r"^[a-zA-Z0-9_]{1,15}$", raw):
        return raw.lower()

    return None


def is_reserved_path(path: str) -> bool:
    """检查是否为 Twitter 保留路径

    Twitter 保留路径不能作为用户名使用。

    Args:
        path: 路径名称

    Returns:
        是否为保留路径

    Examples:
        >>> is_reserved_path("home")
        True
        >>> is_reserved_path("elonmusk")
        False
        >>> is_reserved_path("SETTINGS")
        True
    """
    return path.lower() in C.TWITTER_RESERVED_PATHS


__all__ = ["validate_username", "clean_username", "is_reserved_path"]
