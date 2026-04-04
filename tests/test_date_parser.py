# -*- coding: utf-8 -*-
"""DateParser 测试

测试 DateParser 的日期解析功能。
"""

from datetime import datetime, timedelta

from tmdc.parsers import DateParser


class TestDateParser:
    """DateParser 测试类"""

    def test_parse_relative_days(self):
        """解析相对天数"""
        result = DateParser.parse("7d")
        assert result is not None
        expected = datetime.now() - timedelta(days=7)
        assert abs((result - expected).total_seconds()) < 2

    def test_parse_relative_weeks(self):
        """解析相对周数"""
        result = DateParser.parse("2w")
        assert result is not None
        expected = datetime.now() - timedelta(weeks=2)
        assert abs((result - expected).total_seconds()) < 2

    def test_parse_relative_months(self):
        """解析相对月数（30天）"""
        result = DateParser.parse("1m")
        assert result is not None
        expected = datetime.now() - timedelta(days=30)
        assert abs((result - expected).total_seconds()) < 2

    def test_parse_relative_hours(self):
        """解析相对小时数"""
        result = DateParser.parse("12h")
        assert result is not None
        expected = datetime.now() - timedelta(hours=12)
        assert abs((result - expected).total_seconds()) < 2

    def test_parse_yesterday(self):
        """解析 yesterday"""
        result = DateParser.parse("yesterday")
        assert result is not None
        expected = datetime.now() - timedelta(days=1)
        expected = expected.replace(hour=0, minute=0, second=0, microsecond=0)
        assert result.year == expected.year
        assert result.month == expected.month
        assert result.day == expected.day

    def test_parse_today(self):
        """解析 today"""
        result = DateParser.parse("today")
        assert result is not None
        now = datetime.now()
        assert result.year == now.year
        assert result.month == now.month
        assert result.day == now.day
        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0

    def test_parse_now(self):
        """解析 now"""
        result = DateParser.parse("now")
        assert result is not None
        now = datetime.now()
        assert abs((result - now).total_seconds()) < 2

    def test_parse_absolute_date(self):
        """解析绝对日期"""
        result = DateParser.parse("2024-01-15")
        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_parse_absolute_datetime(self):
        """解析绝对日期时间"""
        result = DateParser.parse("2024-01-15 10:30:00")
        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 10
        assert result.minute == 30
        assert result.second == 0

    def test_parse_absolute_datetime_short(self):
        """解析绝对日期时间（无秒）"""
        result = DateParser.parse("2024-01-15 10:30")
        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 10
        assert result.minute == 30

    def test_parse_absolute_date_slash(self):
        """解析斜线分隔的日期"""
        result = DateParser.parse("2024/01/15")
        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_parse_month_day_only(self):
        """解析月-日格式"""
        result = DateParser.parse("01-15")
        assert result is not None
        now = datetime.now()
        assert result.month == 1
        assert result.day == 15
        assert result.year == now.year

    def test_parse_month_day_slash(self):
        """解析斜线分隔的月-日"""
        result = DateParser.parse("12/25")
        assert result is not None
        now = datetime.now()
        assert result.month == 12
        assert result.day == 25

    def test_parse_empty_returns_none(self):
        """空输入返回 None"""
        assert DateParser.parse("") is None
        assert DateParser.parse("   ") is None
        assert DateParser.parse(None) is None

    def test_parse_invalid_returns_none(self):
        """无效输入返回 None"""
        assert DateParser.parse("invalid") is None
        assert DateParser.parse("abc123") is None
        assert DateParser.parse("not-a-date") is None
        assert DateParser.parse("2024-13-45") is None

    def test_parse_trims_whitespace(self):
        """解析前去除空白"""
        result = DateParser.parse("  7d  ")
        assert result is not None

    def test_parse_case_insensitive(self):
        """解析不区分大小写"""
        result_lower = DateParser.parse("today")
        result_upper = DateParser.parse("TODAY")
        assert result_lower is not None
        assert result_upper is not None
        assert result_lower.replace(microsecond=0) == result_upper.replace(microsecond=0)
