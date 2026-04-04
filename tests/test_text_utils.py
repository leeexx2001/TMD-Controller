# -*- coding: utf-8 -*-
"""测试 text_utils.py"""

import pytest

from tmdc.utils.text_utils import (
    escape_like_pattern,
    safe_join,
)


class TestEscapeLikePattern:
    """LIKE 模式转义测试"""

    def test_escape_percent(self):
        """测试转义百分号"""
        result = escape_like_pattern("100%")
        assert result == r"%100\%%"

    def test_escape_underscore(self):
        """测试转义下划线"""
        result = escape_like_pattern("test_user")
        assert result == r"%test\_user%"

    def test_escape_backslash(self):
        """测试转义反斜杠"""
        result = escape_like_pattern("path\\file")
        assert result == r"%path\\file%"

    def test_normal_text(self):
        """测试普通文本"""
        result = escape_like_pattern("normal")
        assert result == "%normal%"

    def test_empty_string(self):
        """测试空字符串"""
        result = escape_like_pattern("")
        assert result == "%%"

    def test_combined_special_chars(self):
        """测试混合特殊字符"""
        result = escape_like_pattern("test_user%complete")
        assert "\\" in result
        assert result.startswith("%")
        assert result.endswith("%")


class TestSafeJoin:
    """安全连接测试"""

    def test_basic_join(self):
        """测试基本连接"""
        result = safe_join(["a", "b", "c"])
        assert result == "a, b, c"

    def test_custom_separator(self):
        """测试自定义分隔符"""
        result = safe_join(["a", "b", "c"], separator=" | ")
        assert result == "a | b | c"

    def test_empty_list(self):
        """测试空列表"""
        assert safe_join([]) == ""

    def test_none_list(self):
        """测试 None 列表"""
        assert safe_join(None) == ""

    def test_filter_empty_values(self):
        """测试过滤空值"""
        result = safe_join(["a", "", "b", None, "c"])
        assert result == "a, b, c"

    def test_single_item(self):
        """测试单个项目"""
        assert safe_join(["only"]) == "only"
