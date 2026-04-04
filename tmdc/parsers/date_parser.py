# -*- coding: utf-8 -*-
"""
日期解析器模块

提供日期输入解析功能，支持相对时间和绝对时间格式。
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Optional


class DateParser:
    """日期解析器

    解析用户输入的日期/时间字符串，支持多种格式。

    支持的格式：
    - 相对时间: 7d (7天前), 2w (2周前), 1m (1月前), 12h (12小时前)
    - 关键词: yesterday, today, now
    - 绝对时间: 2024-01-15, 2024-01-15 10:30, 2024/01/15
    """

    @classmethod
    def parse(cls, input_str: str) -> Optional[datetime]:
        """解析用户输入的日期/时间字符串

        Args:
            input_str: 用户输入的日期/时间字符串

        Returns:
            datetime 对象，如果解析失败则返回 None
        """
        if not input_str or not input_str.strip():
            return None

        input_str = input_str.strip().lower()
        now = datetime.now()

        relative_patterns = {
            r"^(\d+)d$": lambda x: now - timedelta(days=int(x)),
            r"^(\d+)w$": lambda x: now - timedelta(weeks=int(x)),
            r"^(\d+)m$": lambda x: now - timedelta(days=int(x) * 30),
            r"^(\d+)h$": lambda x: now - timedelta(hours=int(x)),
            r"^yesterday$": lambda _: now - timedelta(days=1),
            r"^today$": lambda _: now.replace(hour=0, minute=0, second=0, microsecond=0),
            r"^now$": lambda _: now,
        }

        for pattern, handler in relative_patterns.items():
            match = re.match(pattern, input_str)
            if match:
                result = handler(match.group(1) if match.groups() else None)
                return result.replace(microsecond=0)

        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%Y/%m/%d %H:%M:%S",
            "%Y/%m/%d %H:%M",
            "%Y/%m/%d",
            "%m-%d",
            "%m/%d",
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(input_str, fmt)

                if "%Y" not in fmt:
                    dt = dt.replace(year=now.year)
                    if dt > now:
                        dt = dt.replace(year=now.year - 1)

                return dt

            except ValueError:
                continue

        return None


__all__ = ["DateParser"]
