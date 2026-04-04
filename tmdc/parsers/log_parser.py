# -*- coding: utf-8 -*-
"""
TMD 日志解析器模块

"""

from __future__ import annotations

# 标准库
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Pattern, Tuple

if TYPE_CHECKING:
    pass

# 第三方库（无）

# 本地模块
from ..tmd_types import DownloadResult
from ..utils.patterns import (
    LOG_ERROR_RE,
    LOG_ERROR_USER_RE,
    LOG_FAILED_USER_RE,
    LOG_FATAL_RE,
    LOG_WARN_USER_OLD_RE,
    LOG_WARN_USER_RE,
)


class TMDLogParser:
    """
    TMD 核心日志解析器

    解析 TMD 命令行工具的输出日志，提取警告和错误信息。

    Example:
        >>> parser = TMDLogParser(Path("tmd.log"))
        >>> result = parser.parse_increment(0)
        >>> print(f"警告用户: {result.warn_users}")
        >>> print(f"错误消息: {result.error_messages}")
    """

    WARN_PATTERNS: Tuple[Pattern[str], ...] = (
        LOG_WARN_USER_RE,
        LOG_WARN_USER_OLD_RE,
        LOG_FAILED_USER_RE,
        LOG_ERROR_USER_RE,
    )
    """警告模式列表"""

    ERROR_PATTERNS: Tuple[Pattern[str], ...] = (
        LOG_ERROR_RE,
        LOG_FATAL_RE,
    )
    """错误模式列表"""

    def __init__(self, log_path: Path) -> None:
        """
        初始化日志解析器

        Args:
            log_path: 日志文件路径
        """
        self.log_path = log_path
        self.last_error: Optional[str] = None

    def get_size(self) -> int:
        """
        获取日志文件大小

        Returns:
            文件大小（字节），如果文件不存在则返回 0
        """
        if self.log_path.exists():
            return self.log_path.stat().st_size
        return 0

    def read_increment(self, start_pos: int) -> str:
        """
        增量读取日志内容

        从指定位置开始读取日志文件的新内容。

        Args:
            start_pos: 起始位置（字节偏移）

        Returns:
            读取到的内容，如果读取失败则返回空字符串
        """
        if not self.log_path.exists():
            return ""
        try:
            with open(self.log_path, "r", encoding="utf-8", errors="ignore") as f:
                f.seek(start_pos)
                return f.read()
        except Exception as e:
            self.last_error = str(e)
            return ""

    def parse(self, log_content: str) -> DownloadResult:
        """
        解析日志内容

        从日志内容中提取警告用户和错误消息。

        Args:
            log_content: 日志内容

        Returns:
            DownloadResult: 解析结果
        """
        result = DownloadResult(raw_output=log_content)

        if not log_content:
            return result

        # 提取警告用户
        for pattern in self.WARN_PATTERNS:
            result.warn_users.extend(pattern.findall(log_content))
        result.warn_users = list(set(result.warn_users))
        result.warn_count = len(result.warn_users)

        # 提取错误消息
        for pattern in self.ERROR_PATTERNS:
            result.error_messages.extend(pattern.findall(log_content))
        result.error_count = len(result.error_messages)

        return result

    def parse_increment(self, start_pos: int) -> DownloadResult:
        """
        增量解析日志

        从指定位置开始读取并解析日志。

        Args:
            start_pos: 起始位置（字节偏移）

        Returns:
            DownloadResult: 解析结果
        """
        return self.parse(self.read_increment(start_pos))

    def get_tail(self, lines: int = 50) -> str:
        """
        获取日志尾部内容

        Args:
            lines: 行数

        Returns:
            日志尾部内容
        """
        if not self.log_path.exists():
            return ""

        try:
            with open(self.log_path, "r", encoding="utf-8", errors="ignore") as f:
                all_lines = f.readlines()
                return "".join(all_lines[-lines:])
        except Exception as e:
            self.last_error = str(e)
            return ""

    def clear(self) -> bool:
        """
        清空日志文件

        Returns:
            操作是否成功
        """
        try:
            with open(self.log_path, "w", encoding="utf-8") as f:
                f.truncate()
            return True
        except Exception as e:
            self.last_error = str(e)
            return False


__all__ = ["TMDLogParser"]
