# -*- coding: utf-8 -*-
"""
TMD 输入解析器模块

提供智能输入识别和解析功能，支持：
- Twitter/X 用户链接解析
- Twitter/X 列表链接解析
- 批量输入处理

"""

from __future__ import annotations

# 标准库
import re
from typing import List, Tuple

# 本地模块
from ..constants import C
from ..tmd_types import IInputParser
from ..utils.patterns import (
    TWITTER_LIST_URL_RE,
    TWITTER_LIST_URL_ALT_RE,
    TWITTER_USER_URL_RE,
    TWITTER_USER_URL_WITH_PATH_RE,
    USERNAME_IN_PARENS_RE,
)
from ..utils.validators.username import is_reserved_path

# 第三方库（无）


class InputParser(IInputParser):
    """
    智能输入识别系统

    解析各种输入格式，包括用户名、列表 ID、URL 等。

    Attributes:
        LIST_URL_PATTERNS: 列表 URL 匹配模式列表
        USER_URL_PATTERNS: 用户 URL 匹配模式列表
        PARENTHESIS_SUFFIX_RE: 括号后缀匹配模式

    Example:
        >>> result = InputParser.parse("https://twitter.com/username")
        >>> result
        ('user', 'username', 'https://twitter.com/username')

        >>> result = InputParser.parse("1234567890123")
        >>> result
        ('list', '1234567890123', '1234567890123')
    """

    # 列表 URL 匹配模式（从 patterns 模块导入）
    LIST_URL_PATTERNS: Tuple[re.Pattern[str], ...] = (
        TWITTER_LIST_URL_RE,
        TWITTER_LIST_URL_ALT_RE,
    )

    # 用户 URL 匹配模式（从 patterns 模块导入）
    USER_URL_PATTERNS: Tuple[re.Pattern[str], ...] = (
        TWITTER_USER_URL_RE,
        TWITTER_USER_URL_WITH_PATH_RE,
    )

    # 括号后缀匹配模式（从 patterns 模块导入）
    PARENTHESIS_SUFFIX_RE: re.Pattern[str] = USERNAME_IN_PARENS_RE

    @classmethod
    def parse(cls, input_str: str) -> Tuple[str, str, str]:
        """
        解析输入字符串

        识别输入类型并提取关键信息。

        Args:
            input_str: 输入字符串，可以是用户名、URL、列表 ID 等

        Returns:
            元组 (类型, 值, 原始输入):
            - 类型: "user" | "list" | "numeric_id" | "batch" | "unknown"
            - 值: 提取的关键值（用户名、列表 ID 等）
            - 原始输入: 去除首尾空白后的原始字符串

        Example:
            >>> InputParser.parse("@username")
            ('user', 'username', '@username')

            >>> InputParser.parse("https://x.com/i/lists/123456789")
            ('list', '123456789', 'https://x.com/i/lists/123456789')

            >>> InputParser.parse("user1, user2, user3")
            ('batch', 'user1, user2, user3', 'user1, user2, user3')
        """
        if not input_str or not input_str.strip():
            return ("unknown", "", "")

        original = input_str.strip()
        cleaned = original.strip("\"'").strip()

        # 优先匹配列表 URL
        for pattern in cls.LIST_URL_PATTERNS:
            match = pattern.search(cleaned)
            if match:
                return ("list", match.group(1), original)

        # 匹配纯数字（可能是列表 ID 或用户 ID）
        if cleaned.isdigit():
            if len(cleaned) >= C.LIST_ID_MIN_LEN:
                return ("numeric_id", cleaned, original)
            else:
                return ("user", cleaned, original)

        # 匹配用户 URL
        for pattern in cls.USER_URL_PATTERNS:
            match = pattern.search(cleaned)
            if match:
                username = match.group(1).lower()
                if not is_reserved_path(username) and not username.isdigit():
                    return ("user", username, original)

        # 匹配 @username 格式
        if cleaned.startswith("@"):
            username = cleaned[1:].strip()
            if username and not username.startswith("@"):
                return ("user", username, original)

        # 匹配括号后缀格式 "显示名 (username)"
        paren_match = cls.PARENTHESIS_SUFFIX_RE.search(cleaned)
        if paren_match:
            username = paren_match.group(1)
            if (
                len(username) <= C.USERNAME_MAX_LEN
                and not is_reserved_path(username)
                and not username.isdigit()
            ):
                return ("user", username, original)

        # 匹配批量输入（逗号或空格分隔）
        if "," in cleaned or " " in cleaned:
            return ("batch", cleaned, original)

        # 默认作为用户名处理
        username = cleaned.replace("@", "").replace(" ", "").strip()
        if username and len(username) <= C.USERNAME_MAX_LEN and not username.isdigit():
            return ("user", username, original)

        return ("unknown", cleaned, original)

    @classmethod
    def parse_batch(cls, input_str: str) -> List[Tuple[str, str]]:
        """
        解析批量输入（仅支持用户，不支持列表）

        设计原因：
        - 文件批量下载主要用于批量下载用户（如粉丝列表、关注列表导出）
        - 列表下载通常单独处理，且有专门的 [Q] 快速下载功能
        - 用户批量只需 1 次 TMD 调用，列表需要 N 次，性能差异大
        - 用户失败追踪有明确的 warn_users，列表失败追踪不一致

        Args:
            input_str: 批量输入字符串，支持逗号或空格分隔

        Returns:
            去重后的 (类型, 值) 元组列表，类型仅包含 "user"

        Example:
            >>> InputParser.parse_batch("user1, user2, @user3")
            [('user', 'user1'), ('user', 'user2'), ('user', 'user3')]

            >>> InputParser.parse_batch("https://twitter.com/user1 user2")
            [('user', 'user1'), ('user', 'user2')]
        """
        items = re.split(r"[,\s]+", input_str.strip())
        results: List[Tuple[str, str]] = []
        seen: set[str] = set()

        for item in items:
            if not item:
                continue
            type_, value, _ = cls.parse(item)

            # 跳过列表类型
            if type_ == "list":
                continue

            # 数字 ID 作为用户处理
            if type_ == "numeric_id":
                type_ = "user"

            # 去重添加
            if type_ == "user" and value.lower() not in seen:
                results.append((type_, value))
                seen.add(value.lower())

        return results

    # ==================== IInputParser 接口实现 ====================

    @classmethod
    def parse_user_input(cls, input_str: str) -> List[str]:
        """
        解析用户输入

        实现 IInputParser 接口方法。

        Args:
            input_str: 输入字符串

        Returns:
            用户名列表

        Example:
            >>> InputParser.parse_user_input("user1, user2, @user3")
            ['user1', 'user2', 'user3']
        """
        results = cls.parse_batch(input_str)
        return [value for type_, value in results if type_ == "user"]

    @classmethod
    def parse_list_input(cls, input_str: str) -> List[str]:
        """
        解析列表输入

        实现 IInputParser 接口方法。

        Args:
            input_str: 输入字符串

        Returns:
            列表 ID 列表

        Example:
            >>> InputParser.parse_list_input("123456789 987654321")
            ['123456789', '987654321']
        """
        items = re.split(r"[,\s]+", input_str.strip())
        results: List[str] = []
        seen: set[str] = set()

        for item in items:
            if not item:
                continue
            type_, value, _ = cls.parse(item)

            if type_ in ("list", "numeric_id") and value not in seen:
                results.append(value)
                seen.add(value)

        return results


__all__ = ["InputParser"]
