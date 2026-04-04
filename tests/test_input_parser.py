# -*- coding: utf-8 -*-
"""测试 input_parser.py"""

import pytest
from tmdc.parsers.input_parser import InputParser
from tmdc.parsers import DelayParser
from tmdc.utils.validators.cookie import parse_cookie_string


class TestInputParser:
    """输入解析器测试"""

    def test_parse_username_with_at(self):
        """测试 @username 格式"""
        result = InputParser.parse("@testuser")
        assert result == ("user", "testuser", "@testuser")

    def test_parse_username_without_at(self):
        """测试纯用户名格式"""
        result = InputParser.parse("testuser")
        assert result[0] == "user"
        assert result[1] == "testuser"

    def test_parse_listurl(self):
        """测试列表 URL"""
        result = InputParser.parse("https://twitter.com/i/lists/123456789012")
        assert result == ("list", "123456789012", "https://twitter.com/i/lists/123456789012")

    def test_parse_x_listurl(self):
        """测试 x.com 列表 URL"""
        result = InputParser.parse("https://x.com/i/lists/987654321098")
        assert result == ("list", "987654321098", "https://x.com/i/lists/987654321098")

    def test_parse_user_url(self):
        """测试用户 URL"""
        result = InputParser.parse("https://twitter.com/testuser")
        assert result[0] == "user"
        assert result[1] == "testuser"

    def test_parse_numeric_id_as_list(self):
        """测试长数字作为列表 ID"""
        result = InputParser.parse("12345678901234")
        assert result[0] in ("list", "numeric_id")

    def test_parse_empty_input(self):
        """测试空输入"""
        result = InputParser.parse("")
        assert result == ("unknown", "", "")

    def test_parse_batch_input(self):
        """测试批量输入"""
        result = InputParser.parse("user1, user2, user3")
        assert result[0] == "batch"

    def test_parse_parenthesis_format(self):
        """测试括号格式"""
        result = InputParser.parse("Test User (testuser)")
        assert result[0] == "user"
        assert result[1] == "testuser"

    def test_parse_reserved_path(self):
        """测试保留路径"""
        result = InputParser.parse("https://twitter.com/home")
        assert result[0] != "user"

    def test_parse_batch(self):
        """测试批量解析"""
        items = InputParser.parse_batch("user1, user2, @user3")
        assert len(items) == 3
        assert all(item[0] == "user" for item in items)

    def test_parse_batch_with_urls(self):
        """测试批量解析包含 URL"""
        items = InputParser.parse_batch("https://twitter.com/user1 user2")
        assert len(items) == 2


class TestCookieParser:
    """Cookie 解析器测试（迁移到 validators.py）"""

    def test_parse_cookie_string(self):
        """测试 Cookie 字符串解析"""
        cookie_str = "auth_token=abc123def456789012345678901234567890; ct0=789xyz01234567890123456789012345; lang=en"
        result = parse_cookie_string(cookie_str)
        assert result is not None
        assert "auth_token" in result
        assert "ct0" in result

    def test_parse_cookie_string_invalid(self):
        """测试无效 Cookie 字符串"""
        result = parse_cookie_string("invalid cookie")
        assert result is None


class TestDelayParser:
    """延迟解析器测试（迁移到 delay_parser.py）"""

    def test_parse_delay_range(self):
        """测试延迟范围解析"""
        result = DelayParser.parse("5 10")
        assert result == (5, 10)

        result = DelayParser.parse("5-10")
        assert result == (5, 10)

    def test_parse_delay_range_invalid(self):
        """测试无效延迟范围"""
        result = DelayParser.parse("invalid")
        assert result is None
