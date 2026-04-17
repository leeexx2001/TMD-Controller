# -*- coding: utf-8 -*-
"""测试 validators.py"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock

from tmdc.utils.validators.auth import validate_auth_token, validate_ct0
from tmdc.utils.validators.cookie import parse_cookie_string
from tmdc.utils.validators.proxy import check_proxy_values
from tmdc.utils.validators.timestamp import handle_numeric_id_ambiguity, parse_timestamp_target
from tmdc.utils.validators.username import clean_username, is_reserved_path


class TestValidateAuthToken:
    """auth_token 验证测试"""

    def test_valid_token(self):
        """测试有效的 auth_token"""
        valid, msg = validate_auth_token("a" * 40)
        assert valid is True
        assert msg == ""

    def test_empty_token(self):
        """测试空 token"""
        valid, msg = validate_auth_token("")
        assert valid is False
        assert "不能为空" in msg

    def test_short_token(self):
        """测试过短的 token"""
        valid, msg = validate_auth_token("short")
        assert valid is False
        assert "长度过短" in msg

    def test_invalid_chars(self):
        """测试包含非法字符的 token"""
        valid, msg = validate_auth_token("g" * 40)
        assert valid is False
        assert "十六进制" in msg


class TestValidateCt0:
    """ct0 验证测试"""

    def test_valid_ct0(self):
        """测试有效的 ct0"""
        valid, msg = validate_ct0("a" * 64)
        assert valid is True
        assert msg == ""

    def test_empty_ct0(self):
        """测试空 ct0"""
        valid, msg = validate_ct0("")
        assert valid is False
        assert "不能为空" in msg

    def test_short_ct0(self):
        """测试过短的 ct0"""
        valid, msg = validate_ct0("short")
        assert valid is False
        assert "长度过短" in msg


class TestCheckProxyValues:
    """代理配置验证测试"""

    def test_valid_proxy(self):
        """测试有效的代理配置"""
        valid, msg = check_proxy_values("127.0.0.1", 7890, True)
        assert valid is True
        assert msg == ""

    def test_proxy_disabled(self):
        """测试禁用代理"""
        valid, msg = check_proxy_values("", 0, False)
        assert valid is True
        assert msg == ""

    def test_empty_host(self):
        """测试空主机"""
        valid, msg = check_proxy_values("", 7890, True)
        assert valid is False
        assert "不能为空" in msg

    def test_invalid_port(self):
        """测试无效端口"""
        valid, msg = check_proxy_values("127.0.0.1", 99999, True)
        assert valid is False
        assert "超出范围" in msg

    def test_port_not_integer(self):
        """测试非整数端口"""
        valid, msg = check_proxy_values("127.0.0.1", "abc", True)
        assert valid is False
        assert "格式无效" in msg

    def test_host_with_spaces(self):
        """测试包含空格的主机"""
        valid, msg = check_proxy_values("127.0.0.1 test", 7890, True)
        assert valid is False
        assert "非法字符" in msg


class TestCleanUsername:
    """用户名清理测试"""

    def test_clean_with_at(self):
        """测试清理 @ 前缀"""
        assert clean_username("@elonmusk") == "elonmusk"

    def test_clean_from_url(self):
        """测试从 URL 提取用户名"""
        assert clean_username("https://x.com/elonmusk") == "elonmusk"
        assert clean_username("https://twitter.com/elonmusk") == "elonmusk"

    def test_clean_from_parens(self):
        """测试从括号格式提取用户名"""
        assert clean_username("Elon Musk(elonmusk)") == "elonmusk"

    def test_clean_plain_username(self):
        """测试纯用户名"""
        assert clean_username("elonmusk") == "elonmusk"

    def test_clean_empty(self):
        """测试空输入"""
        assert clean_username("") is None
        assert clean_username(None) is None

    def test_clean_invalid(self):
        """测试无效输入"""
        assert clean_username("invalid user!") is None


class TestIsReservedPath:
    """保留路径检查测试"""

    def test_reserved_paths(self):
        """测试保留路径"""
        assert is_reserved_path("home") is True
        assert is_reserved_path("settings") is True
        assert is_reserved_path("login") is True

    def test_case_insensitive(self):
        """测试大小写不敏感"""
        assert is_reserved_path("HOME") is True
        assert is_reserved_path("Settings") is True

    def test_normal_username(self):
        """测试普通用户名"""
        assert is_reserved_path("elonmusk") is False
        assert is_reserved_path("twitter") is False


class TestParseTimestampTarget:
    """时间戳目标解析测试"""

    def test_user_with_time(self):
        """测试用户格式带时间"""
        target, time_part = parse_timestamp_target("user:elonmusk,7d")
        assert target == {"type": "user", "id": "elonmusk"}
        assert time_part == "7d"

    def test_list_with_time(self):
        """测试列表格式带时间"""
        target, time_part = parse_timestamp_target("list:1234567890,2024-01-15")
        assert target == {"type": "list", "id": "1234567890"}
        assert time_part == "2024-01-15"

    def test_at_username(self):
        """测试 @ 用户名格式"""
        target, time_part = parse_timestamp_target("@elonmusk")
        assert target == {"type": "user", "id": "elonmusk"}
        assert time_part is None

    def test_list_only(self):
        """测试仅列表 ID"""
        target, time_part = parse_timestamp_target("list:1234567890")
        assert target == {"type": "list", "id": "1234567890"}
        assert time_part is None

    def test_empty(self):
        """测试空输入"""
        target, time_part = parse_timestamp_target("")
        assert target is None
        assert time_part is None

    def test_invalid_format(self):
        """测试无效格式"""
        target, time_part = parse_timestamp_target("invalid")
        assert target is None
        assert time_part is None


class TestHandleNumericIdAmbiguity:
    """数字 ID 歧义处理测试"""

    def setup_method(self):
        """设置测试方法"""
        self.ui = MagicMock()
        self.test_value = "123456789"

    def test_mode_both_default_as_list_enter(self):
        """测试 mode='both' 默认列表，按回车"""
        self.ui.safe_input.return_value = ""
        result_type, result_value = handle_numeric_id_ambiguity(
            self.test_value, self.ui, default_as_list=True, mode="both"
        )
        assert result_type == "list"
        assert result_value == self.test_value

    def test_mode_both_default_as_list_choose_user(self):
        """测试 mode='both' 默认列表，选择用户"""
        self.ui.safe_input.return_value = "1"
        result_type, result_value = handle_numeric_id_ambiguity(
            self.test_value, self.ui, default_as_list=True, mode="both"
        )
        assert result_type == "user"
        assert result_value == self.test_value

    def test_mode_both_default_as_user_enter(self):
        """测试 mode='both' 默认用户，按回车"""
        self.ui.safe_input.return_value = ""
        result_type, result_value = handle_numeric_id_ambiguity(
            self.test_value, self.ui, default_as_list=False, mode="both"
        )
        assert result_type == "user"
        assert result_value == self.test_value

    def test_mode_both_default_as_user_choose_list(self):
        """测试 mode='both' 默认用户，选择列表"""
        self.ui.safe_input.return_value = "1"
        result_type, result_value = handle_numeric_id_ambiguity(
            self.test_value, self.ui, default_as_list=False, mode="both"
        )
        assert result_type == "list"
        assert result_value == self.test_value

    def test_mode_user_only_confirm(self):
        """测试 mode='user_only' 确认"""
        self.ui.safe_input.return_value = ""
        result_type, result_value = handle_numeric_id_ambiguity(
            self.test_value, self.ui, mode="user_only"
        )
        assert result_type == "user"
        assert result_value == self.test_value

    def test_mode_user_only_cancel(self):
        """测试 mode='user_only' 取消"""
        self.ui.safe_input.return_value = "N"
        result_type, result_value = handle_numeric_id_ambiguity(
            self.test_value, self.ui, mode="user_only"
        )
        assert result_type == ""
        assert result_value == self.test_value

    def test_mode_user_only_cancel_lowercase(self):
        """测试 mode='user_only' 取消（小写 n）"""
        self.ui.safe_input.return_value = "n"
        result_type, result_value = handle_numeric_id_ambiguity(
            self.test_value, self.ui, mode="user_only"
        )
        assert result_type == ""
        assert result_value == self.test_value

    def test_mode_list_only_confirm(self):
        """测试 mode='list_only' 确认"""
        self.ui.safe_input.return_value = ""
        result_type, result_value = handle_numeric_id_ambiguity(
            self.test_value, self.ui, mode="list_only"
        )
        assert result_type == "list"
        assert result_value == self.test_value

    def test_mode_list_only_cancel(self):
        """测试 mode='list_only' 取消"""
        self.ui.safe_input.return_value = "N"
        result_type, result_value = handle_numeric_id_ambiguity(
            self.test_value, self.ui, mode="list_only"
        )
        assert result_type == ""
        assert result_value == self.test_value

    def test_invalid_mode(self):
        """测试无效模式"""
        self.ui.safe_input.return_value = ""
        result_type, result_value = handle_numeric_id_ambiguity(
            self.test_value, self.ui, mode="invalid"
        )
        assert result_type == ""
        assert result_value == self.test_value
