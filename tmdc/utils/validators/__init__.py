# -*- coding: utf-8 -*-
"""验证工具模块

提供各种数据验证功能，包括代理配置、认证令牌、用户名、列表ID、路径等。
"""

from tmdc.utils.validators.auth import validate_auth_token, validate_ct0
from tmdc.utils.validators.username import clean_username, is_reserved_path
from tmdc.utils.validators.proxy import check_proxy_values
from tmdc.utils.validators.timestamp import handle_numeric_id_ambiguity, parse_timestamp_target
from tmdc.utils.validators.cookie import parse_cookie_string

__all__ = [
    "validate_auth_token",
    "validate_ct0",
    "check_proxy_values",
    "clean_username",
    "is_reserved_path",
    "parse_timestamp_target",
    "handle_numeric_id_ambiguity",
    "parse_cookie_string",
]
