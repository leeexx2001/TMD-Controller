# -*- coding: utf-8 -*-
"""测试 formatters.py"""

import pytest
from datetime import datetime, timedelta

from tmdc.utils.formatters import (
    format_duration,
    format_timestamp,
    mask_token,
    format_file_size,
    format_number,
    parse_db_timestamp,
)


class TestFormatDuration:
    """持续时间格式化测试"""

    def test_years(self):
        """测试年份格式化"""
        assert format_duration(timedelta(days=400)) == "1年"
        assert format_duration(timedelta(days=730)) == "2年"

    def test_days(self):
        """测试天数格式化"""
        assert format_duration(timedelta(days=3)) == "3天"
        assert format_duration(timedelta(days=3, hours=5)) == "3天5小时"

    def test_hours(self):
        """测试小时格式化"""
        assert format_duration(timedelta(hours=2)) == "2小时"
        assert format_duration(timedelta(hours=1)) == "1小时"

    def test_minutes(self):
        """测试分钟格式化"""
        assert format_duration(timedelta(minutes=30)) == "30分钟"

    def test_seconds(self):
        """测试秒数格式化"""
        assert format_duration(timedelta(seconds=45)) == "45秒"

    def test_negative_duration(self):
        """测试负数持续时间"""
        result = format_duration(timedelta(seconds=-10))
        assert "未来时间" in result


class TestFormatTimestamp:
    """时间戳格式化测试"""

    def test_none_timestamp(self):
        """测试 None 时间戳"""
        assert format_timestamp(None) == "从未同步"

    def test_empty_string(self):
        """测试空字符串"""
        assert format_timestamp("") == "从未同步"

    def test_datetime_object(self):
        """测试 datetime 对象"""
        dt = datetime(2024, 1, 15, 10, 30, 0)
        result = format_timestamp(dt)
        assert "2024-01-15" in result

    def test_string_timestamp(self):
        """测试字符串时间戳"""
        result = format_timestamp("2024-01-15 10:30:00")
        assert "2024-01-15" in result

    def test_custom_format(self):
        """测试自定义格式"""
        dt = datetime(2024, 1, 15, 10, 30, 0)
        result = format_timestamp(dt, fmt="%Y/%m/%d")
        assert result == "2024/01/15"

    def test_custom_default(self):
        """测试自定义默认值"""
        assert format_timestamp(None, default_empty="未设置") == "未设置"

    def test_timezone_string(self):
        """测试带时区的字符串"""
        result = format_timestamp("2024-01-15 10:30:00+08:00")
        assert "2024-01-15" in result

    def test_z_suffix(self):
        """测试 Z 后缀"""
        result = format_timestamp("2024-01-15 10:30:00Z")
        assert "2024-01-15" in result


class TestMaskToken:
    """Token 脱敏测试"""

    def test_normal_token(self):
        """测试正常 token"""
        result = mask_token("abcdefghijklmnop")
        assert result == "abcdef...mnop"

    def test_short_token(self):
        """测试短 token"""
        assert mask_token("short") == "****"

    def test_empty_token(self):
        """测试空 token"""
        assert mask_token("") == "****"

    def test_none_token(self):
        """测试 None token"""
        assert mask_token(None) == "****"

    def test_exact_length(self):
        """测试刚好 10 位的 token"""
        result = mask_token("abcdefghij")
        assert result == "abcdef...ghij"


class TestFormatFileSize:
    """文件大小格式化测试"""

    def test_zero_bytes(self):
        """测试 0 字节"""
        assert format_file_size(0) == "0 B"

    def test_bytes(self):
        """测试字节"""
        assert format_file_size(512) == "512.00 B"

    def test_kilobytes(self):
        """测试 KB"""
        assert format_file_size(1024) == "1.00 KB"
        assert format_file_size(1536) == "1.50 KB"

    def test_megabytes(self):
        """测试 MB"""
        assert format_file_size(1048576) == "1.00 MB"

    def test_gigabytes(self):
        """测试 GB"""
        assert format_file_size(1073741824) == "1.00 GB"

    def test_terabytes(self):
        """测试 TB"""
        assert format_file_size(1099511627776) == "1.00 TB"

    def test_negative_size(self):
        """测试负数大小"""
        assert format_file_size(-1) == "无效大小"

    def test_custom_precision(self):
        """测试自定义精度"""
        assert format_file_size(1536, precision=0) == "2 KB"
        assert format_file_size(1536, precision=1) == "1.5 KB"


class TestFormatNumber:
    """数字格式化测试"""

    def test_integer(self):
        """测试整数"""
        assert format_number(1234567) == "1,234,567"

    def test_float_with_precision(self):
        """测试浮点数"""
        assert format_number(1234567.89, precision=2) == "1,234,567.89"

    def test_custom_separator(self):
        """测试自定义分隔符"""
        assert format_number(1234567, thousand_separator="_") == "1_234_567"

    def test_float_custom_separator(self):
        """测试浮点数自定义分隔符"""
        result = format_number(1234567.89, precision=2, thousand_separator=".")
        assert "1.234.567,89" in result or result == "1.234.567.89"

    def test_zero(self):
        """测试零"""
        assert format_number(0) == "0"

    def test_negative(self):
        """测试负数"""
        assert format_number(-1234) == "-1,234"


class TestParseDbTimestamp:
    """数据库时间戳解析测试"""

    def test_valid_timestamp(self):
        """测试有效时间戳"""
        result = parse_db_timestamp("2024-01-15 10:30:00")
        assert result == datetime(2024, 1, 15, 10, 30, 0)

    def test_timezone_timestamp(self):
        """测试带时区的时间戳"""
        result = parse_db_timestamp("2024-01-15 10:30:00+08:00")
        assert result == datetime(2024, 1, 15, 10, 30, 0)

    def test_z_suffix(self):
        """测试 Z 后缀"""
        result = parse_db_timestamp("2024-01-15 10:30:00Z")
        assert result == datetime(2024, 1, 15, 10, 30, 0)

    def test_none(self):
        """测试 None"""
        assert parse_db_timestamp(None) is None

    def test_empty_string(self):
        """测试空字符串"""
        assert parse_db_timestamp("") is None
        assert parse_db_timestamp("   ") is None

    def test_invalid_format(self):
        """测试无效格式"""
        assert parse_db_timestamp("invalid") is None
        assert parse_db_timestamp("2024/01/15") is None
