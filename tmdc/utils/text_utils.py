# -*- coding: utf-8 -*-
"""
文本处理工具模块

提供文本处理相关功能，包括 LIKE 模式转义、字符串清理、中文字符宽度计算等。
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


def display_width(s: str) -> int:
    """计算字符串的显示宽度（考虑中文字符）

    中文字符占2个字符宽度，英文字符占1个字符宽度。
    用于终端对齐显示。

    Args:
        s: 输入字符串

    Returns:
        字符串的显示宽度

    Examples:
        >>> display_width("hello")
        5
        >>> display_width("你好")
        4
        >>> display_width("hello世界")
        9
    """
    width = 0
    for char in s:
        if ord(char) > 127:  # 中文字符
            width += 2
        else:
            width += 1
    return width


__all__ = [
    "escape_like_pattern",
    "display_width",
]
