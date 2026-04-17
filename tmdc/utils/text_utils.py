# -*- coding: utf-8 -*-
"""
文本处理工具模块

提供文本处理相关功能，包括 LIKE 模式转义、字符串清理等。
"""

from __future__ import annotations

# 标准库
from typing import List, Optional


def escape_like_pattern(keyword: str, escape_char: str = "\\") -> str:
    """转义 SQL LIKE 通配符

    将 SQL LIKE 查询中的特殊字符（%、_、\\）进行转义，
    确保关键词中的这些字符被当作普通字符匹配。

    Args:
        keyword: 原始关键词
        escape_char: 转义字符，默认为反斜杠

    Returns:
        转义后的模式字符串（已添加前后通配符）

    Examples:
        >>> escape_like_pattern("test_user")
        '%test\\_user%'
        >>> escape_like_pattern("100%")
        '%100\\%%'
        >>> escape_like_pattern("path\\file")
        '%path\\\\file%'
    """
    escaped = keyword.replace("\\", "\\\\").replace("%", r"\%").replace("_", r"\_")
    return f"%{escaped}%"


__all__ = [
    "escape_like_pattern",
]
