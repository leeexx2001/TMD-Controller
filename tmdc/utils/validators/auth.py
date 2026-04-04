# -*- coding: utf-8 -*-
"""认证 Token 验证模块"""

from __future__ import annotations

from typing import Tuple

from ..patterns import HEX_STRING_RE


def validate_auth_token(token: str) -> Tuple[bool, str]:
    """验证 auth_token 格式（Twitter: 40位十六进制）

    Args:
        token: 需要验证的 auth_token 字符串

    Returns:
        Tuple[bool, str]: (是否有效, 错误信息)

    Examples:
        >>> validate_auth_token("a" * 40)
        (True, '')
        >>> validate_auth_token("short")
        (False, '长度过短 (5), 疑似无效 token')
        >>> validate_auth_token("")
        (False, '不能为空')
    """
    if not token:
        return False, "不能为空"

    min_length = 20
    if len(token) < min_length:
        return False, f"长度过短 ({len(token)}), 疑似无效 token"

    if not HEX_STRING_RE.match(token):
        return False, "只能包含十六进制字符 (0-9, a-f)"

    return True, ""


def validate_ct0(ct0: str) -> Tuple[bool, str]:
    """验证 ct0 格式（Twitter CSRF token: 通常64+位十六进制）

    Args:
        ct0: 需要验证的 ct0 字符串

    Returns:
        Tuple[bool, str]: (是否有效, 错误信息)

    Examples:
        >>> validate_ct0("a" * 64)
        (True, '')
        >>> validate_ct0("short")
        (False, '长度过短 (5), 疑似无效 ct0')
    """
    if not ct0:
        return False, "不能为空"

    min_length = 32
    if len(ct0) < min_length:
        return False, f"长度过短 ({len(ct0)}), 疑似无效 ct0"

    if not HEX_STRING_RE.match(ct0):
        return False, "只能包含十六进制字符 (0-9, a-f)"

    return True, ""


__all__ = ["validate_auth_token", "validate_ct0"]
