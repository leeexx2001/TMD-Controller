# -*- coding: utf-8 -*-
"""
格式化工具模块

提供各种数据格式化功能，包括时间戳、持续时间、文件大小、数字等。
"""

# 标准库
from datetime import datetime, timedelta
from typing import Any, Optional, Union

# 第三方库（无）

# 本地模块（无）


def format_duration(td: timedelta) -> str:
    """格式化时间间隔为人类可读字符串

    Args:
        td: 时间间隔

    Returns:
        人类可读的持续时间字符串，如 "2年"、"3天"、"5小时"

    Examples:
        >>> from datetime import timedelta
        >>> format_duration(timedelta(days=400))
        '1年'
        >>> format_duration(timedelta(days=3, hours=5))
        '3天5小时'
        >>> format_duration(timedelta(hours=2))
        '2小时'
    """
    if td.total_seconds() < 0:
        return "0秒 (未来时间)"

    days = td.days
    seconds = td.seconds

    if days >= 365:
        return f"{days // 365}年"
    elif days >= 1:
        hours = seconds // 3600
        return f"{days}天{hours}小时" if hours > 0 else f"{days}天"
    elif seconds >= 3600:
        return f"{seconds // 3600}小时"
    elif seconds >= 60:
        return f"{seconds // 60}分钟"
    else:
        return f"{seconds}秒"


def format_timestamp(
    timestamp: Optional[Any], default_empty: str = "从未同步", fmt: str = "%Y-%m-%d %H:%M:%S"
) -> str:
    """格式化时间戳显示

    Args:
        timestamp: 时间戳值（可以是字符串、datetime 或其他类型）
        default_empty: 当时间戳为空时的默认显示文本
        fmt: 输出格式字符串，默认为 "%Y-%m-%d %H:%M:%S"

    Returns:
        格式化后的显示字符串

    Examples:
        >>> format_timestamp(None)
        '从未同步'
        >>> format_timestamp("2024-01-15 10:30:00")
        '2024-01-15 10:30:00'
        >>> from datetime import datetime
        >>> format_timestamp(datetime(2024, 1, 15, 10, 30, 0))
        '2024-01-15 10:30:00'
    """
    if not timestamp:
        return default_empty

    # 如果已经是 datetime 对象
    if isinstance(timestamp, datetime):
        try:
            return timestamp.strftime(fmt)
        except (TypeError, ValueError):
            return "已设置"

    # 如果是字符串，尝试解析并重新格式化
    if isinstance(timestamp, str):
        timestamp = timestamp.strip()
        if not timestamp:
            return default_empty

        # 尝试处理带时区的格式
        ts_str = timestamp
        if "+" in ts_str or ts_str.endswith("Z"):
            if "+" in ts_str:
                ts_str = ts_str[: ts_str.rfind("+")]
            elif ts_str.endswith("Z"):
                ts_str = ts_str[:-1]

        # 尝试解析常见格式
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
        ]

        for f in formats:
            try:
                dt = datetime.strptime(ts_str.strip(), f)
                return dt.strftime(fmt)
            except ValueError:
                continue

        # 解析失败，返回原始字符串
        return timestamp

    # 其他类型，尝试转为字符串
    try:
        return str(timestamp)
    except (TypeError, ValueError):
        return "已设置"


def mask_token(token: str) -> str:
    """脱敏显示 Token

    将敏感的 token 字符串进行部分隐藏，只显示前6位和后4位。

    Args:
        token: 需要脱敏的 token 字符串

    Returns:
        脱敏后的字符串，如 "abc123...xyz9"

    Examples:
        >>> mask_token("abcdefghijklmnop")
        'abcdef...mnop'
        >>> mask_token("short")
        '****'
        >>> mask_token("")
        '****'
    """
    if not token or len(token) < 10:
        return "****"
    return f"{token[:6]}...{token[-4:]}"


def parse_db_timestamp(ts_str: Optional[str]) -> Optional[datetime]:
    """解析数据库中的时间戳字符串

    支持格式:
        - 2026-01-22 00:00:00+08:00  (带时区)
        - 2026-01-22 00:00:00         (不带时区)

    Args:
        ts_str: 时间戳字符串

    Returns:
        datetime 对象，如果解析失败则返回 None

    Examples:
        >>> parse_db_timestamp("2024-01-15 10:30:00")
        datetime.datetime(2024, 1, 15, 10, 30, 0)
        >>> parse_db_timestamp("2024-01-15 10:30:00+08:00")
        datetime.datetime(2024, 1, 15, 10, 30, 0)
        >>> parse_db_timestamp(None)
        None
    """
    if not ts_str:
        return None

    ts_str = ts_str.strip()
    if not ts_str:
        return None

    try:
        if "+" in ts_str or ts_str.endswith("Z"):
            if "+" in ts_str:
                ts_str = ts_str[: ts_str.rfind("+")]
            elif ts_str.endswith("Z"):
                ts_str = ts_str[:-1]

        return datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


__all__ = [
    "format_duration",
    "format_timestamp",
    "mask_token",
    "parse_db_timestamp",
]
