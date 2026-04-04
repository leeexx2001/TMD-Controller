# -*- coding: utf-8 -*-
"""
正则模式集中定义模块

统一管理项目中使用的正则表达式模式，避免重复定义。
"""

from __future__ import annotations

import re

# Twitter 用户名最大长度常量
USERNAME_MAX_LEN: int = 15

# ==================== Cookie 相关模式 ====================

COOKIE_AUTH_TOKEN_RE: re.Pattern[str] = re.compile(r"auth_token=([a-f0-9]+)", re.IGNORECASE)
"""匹配 auth_token Cookie 值"""

COOKIE_CT0_RE: re.Pattern[str] = re.compile(r"ct0=([a-f0-9]+)", re.IGNORECASE)
"""匹配 ct0 Cookie 值"""

# ==================== 用户名相关模式 ====================

USERNAME_RE: re.Pattern[str] = re.compile(r"^[a-zA-Z0-9_]+$")
"""验证 Twitter 用户名格式"""

USERNAME_IN_PARENS_RE: re.Pattern[str] = re.compile(rf"\(([a-zA-Z0-9_]{{1,{USERNAME_MAX_LEN}}})\)$")
"""匹配括号中的用户名（如 "显示名(username)"）"""

# ==================== URL 相关模式 ====================

TWITTER_LIST_URL_RE: re.Pattern[str] = re.compile(
    r"(?:https?://)?(?:www\.)?(?:twitter\.com|x\.com)/i/lists/(\d+)",
    re.IGNORECASE,
)
"""匹配 Twitter/X 列表 URL"""

TWITTER_LIST_URL_ALT_RE: re.Pattern[str] = re.compile(
    r"(?:https?://)?(?:www\.)?(?:twitter\.com|x\.com)/lists/(\d+)",
    re.IGNORECASE,
)
"""匹配 Twitter/X 列表 URL（备用格式）"""

TWITTER_USER_URL_RE: re.Pattern[str] = re.compile(
    r"(?:https?://)?(?:www\.)?(?:twitter\.com|x\.com)/([a-zA-Z0-9_]{1,15})/?",
    re.IGNORECASE,
)
"""匹配 Twitter/X 用户主页 URL"""

TWITTER_USER_URL_WITH_PATH_RE: re.Pattern[str] = re.compile(
    r"(?:https?://)?(?:www\.)?(?:twitter\.com|x\.com)/([a-zA-Z0-9_]{1,15})/(?:status|with_replies|media|likes)/?",
    re.IGNORECASE,
)
"""匹配 Twitter/X 用户带路径的 URL（如 status、media 等）"""

URL_PATTERN_RE: re.Pattern[str] = re.compile(
    r"(https?|ftp|file)://[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|]"
)
"""匹配通用 URL 格式"""

# ==================== 文件名相关模式 ====================

WIN_INVALID_CHARS_RE: re.Pattern[str] = re.compile(r"[/\\:*?\"<>|]")
"""匹配 Windows 文件名非法字符"""

# ==================== 日志解析相关模式 ====================

LOG_WARN_USER_RE: re.Pattern[str] = re.compile(
    r"failed to get user medias.*?user=([a-zA-Z0-9_]{1,15})",
    re.IGNORECASE,
)
"""匹配日志中的用户警告（新格式）"""

LOG_WARN_USER_OLD_RE: re.Pattern[str] = re.compile(
    r'failed to get user medias.*?user="[^"]*\(([a-zA-Z0-9_]{1,15})\)"',
    re.IGNORECASE,
)
"""匹配日志中的用户警告（旧格式）"""

LOG_ERROR_RE: re.Pattern[str] = re.compile(r"ERROR\[[^\]]+\]\s*(.+?)(?:\n|$)")
"""匹配日志中的 ERROR 级别消息"""

LOG_FATAL_RE: re.Pattern[str] = re.compile(r"FATA\[[^\]]+\]\s*(.+?)(?:\n|$)")
"""匹配日志中的 FATAL 级别消息"""

LOG_FAILED_USER_RE: re.Pattern[str] = re.compile(
    r"FATA\[[^\]]+\].*?failed to get user \[([a-zA-Z0-9_]{1,15})\]", re.IGNORECASE
)
"""匹配日志中 failed to get user 警告（FATA 级别）"""

LOG_ERROR_USER_RE: re.Pattern[str] = re.compile(
    r"ERROR\[[^\]]+\].*?failed to get user \[([a-zA-Z0-9_]{1,15})\]", re.IGNORECASE
)
"""匹配日志中 failed to get user 警告（ERROR 级别）"""

# ==================== 验证相关模式 ====================

HEX_STRING_RE: re.Pattern[str] = re.compile(r"^[a-f0-9]+$", re.IGNORECASE)
"""验证十六进制字符串"""

__all__ = [
    "COOKIE_AUTH_TOKEN_RE",
    "COOKIE_CT0_RE",
    "USERNAME_RE",
    "USERNAME_IN_PARENS_RE",
    "TWITTER_LIST_URL_RE",
    "TWITTER_LIST_URL_ALT_RE",
    "TWITTER_USER_URL_RE",
    "TWITTER_USER_URL_WITH_PATH_RE",
    "URL_PATTERN_RE",
    "WIN_INVALID_CHARS_RE",
    "LOG_WARN_USER_RE",
    "LOG_WARN_USER_OLD_RE",
    "LOG_ERROR_RE",
    "LOG_FATAL_RE",
    "LOG_FAILED_USER_RE",
    "LOG_ERROR_USER_RE",
    "HEX_STRING_RE",
]
