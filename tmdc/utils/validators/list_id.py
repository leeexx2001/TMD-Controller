# -*- coding: utf-8 -*-
"""列表 ID 验证模块"""

from __future__ import annotations

from typing import Tuple


def validate_list_id(list_id: str) -> Tuple[bool, str]:
    """验证 Twitter 列表 ID 格式

    列表 ID 规则：
    - 必须是纯数字
    - 长度至少 10 位

    Args:
        list_id: 需要验证的列表 ID

    Returns:
        Tuple[bool, str]: (是否有效, 错误信息)

    Examples:
        >>> validate_list_id("1234567890")
        (True, '')
        >>> validate_list_id("123")
        (False, '列表 ID 长度过短（至少10位数字）')
        >>> validate_list_id("abc123")
        (False, '列表 ID 必须为纯数字')
    """
    if not list_id:
        return False, "列表 ID 不能为空"

    list_id = str(list_id).strip()

    if not list_id.isdigit():
        return False, "列表 ID 必须为纯数字"

    if len(list_id) < 10:
        return False, "列表 ID 长度过短（至少10位数字）"

    return True, ""


__all__ = ["validate_list_id"]
