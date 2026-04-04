# -*- coding: utf-8 -*-
"""延迟范围解析器模块"""

from __future__ import annotations

from typing import Optional, Tuple


class DelayParser:
    """延迟范围解析器

    解析用户输入的延迟范围字符串，支持多种格式。

    支持的格式：
    - 单个数字: "5" -> (5, 5)
    - 空格分隔: "4 9" -> (4, 9)
    - 连字符分隔: "4-9" -> (4, 9)
    """

    @classmethod
    def parse(cls, input_str: str) -> Optional[Tuple[int, int]]:
        """解析延迟范围输入

        Args:
            input_str: 延迟范围字符串

        Returns:
            (最小值, 最大值) 元组，如果解析失败则返回 None

        Examples:
            >>> DelayParser.parse("5")
            (5, 5)

            >>> DelayParser.parse("4 9")
            (4, 9)

            >>> DelayParser.parse("4-9")
            (4, 9)

            >>> DelayParser.parse("9 4")  # 自动排序
            (4, 9)

            >>> DelayParser.parse("invalid") is None
            True
        """
        if not input_str or not input_str.strip():
            return None

        cleaned = input_str.strip().replace("-", " ")
        parts = cleaned.split()

        if len(parts) == 1:
            try:
                val = int(parts[0])
                return (max(0, val), max(0, val))
            except ValueError:
                return None
        elif len(parts) >= 2:
            try:
                min_val = int(parts[0])
                max_val = int(parts[1])
                min_val = max(0, min_val)
                max_val = max(0, max_val)
                if min_val > max_val:
                    min_val, max_val = max_val, min_val
                return (min_val, max_val)
            except ValueError:
                return None
        return None


__all__ = ["DelayParser"]
