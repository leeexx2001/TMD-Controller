# -*- coding: utf-8 -*-
"""工具模块

提供格式化、验证、文件操作、路径处理等通用工具函数。

模块结构：
- file_io: 文件 I/O 操作
- path_utils: 路径处理工具
- formatters: 格式化工具
- validators: 验证工具
- text_utils: 文本处理工具
- patterns: 正则模式集中定义
"""

from tmdc.utils.file_io import (
    atomic_write_yaml,
    backup_foo_db,
    ensure_dir,
    get_errors_json_path,
    get_file_size,
    read_file_lines,
)
from tmdc.utils.formatters import (
    format_duration,
    format_file_size,
    format_number,
    format_timestamp,
    mask_token,
    parse_db_timestamp,
)
from tmdc.utils.path_utils import (
    generate_filename_from_text,
    get_ext_from_url,
    sanitize_win_filename,
    unique_path,
)
from tmdc.utils.patterns import (
    COOKIE_AUTH_TOKEN_RE,
    COOKIE_CT0_RE,
    HEX_STRING_RE,
    LOG_ERROR_RE,
    LOG_ERROR_USER_RE,
    LOG_FAILED_USER_RE,
    LOG_FATAL_RE,
    LOG_WARN_USER_OLD_RE,
    LOG_WARN_USER_RE,
    TWITTER_LIST_URL_ALT_RE,
    TWITTER_LIST_URL_RE,
    TWITTER_USER_URL_RE,
    TWITTER_USER_URL_WITH_PATH_RE,
    URL_PATTERN_RE,
    USERNAME_IN_PARENS_RE,
    USERNAME_RE,
    WIN_INVALID_CHARS_RE,
)
from tmdc.utils.text_utils import (
    escape_like_pattern,
    safe_join,
)
from tmdc.utils.validators.auth import validate_auth_token, validate_ct0
from tmdc.utils.validators.cookie import parse_cookie_string
from tmdc.utils.validators.list_id import validate_list_id
from tmdc.utils.validators.path import validate_path
from tmdc.utils.validators.proxy import check_proxy_values
from tmdc.utils.validators.timestamp import handle_numeric_id_ambiguity, parse_timestamp_target
from tmdc.utils.validators.username import clean_username, validate_username

__all__ = [
    # 文件 I/O 工具
    "atomic_write_yaml",
    "backup_foo_db",
    "ensure_dir",
    "get_file_size",
    "get_errors_json_path",
    "read_file_lines",
    # 路径处理工具
    "sanitize_win_filename",
    "unique_path",
    "get_ext_from_url",
    "generate_filename_from_text",
    # 格式化工具
    "format_duration",
    "format_file_size",
    "format_number",
    "format_timestamp",
    "mask_token",
    "parse_db_timestamp",
    # 验证工具
    "check_proxy_values",
    "clean_username",
    "handle_numeric_id_ambiguity",
    "parse_cookie_string",
    "parse_timestamp_target",
    "validate_auth_token",
    "validate_ct0",
    "validate_list_id",
    "validate_path",
    "validate_username",
    # 文本处理工具
    "escape_like_pattern",
    "safe_join",
    # 正则模式
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
