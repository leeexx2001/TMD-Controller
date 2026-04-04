# -*- coding: utf-8 -*-
"""测试 tmd_types.py"""

import pytest
from datetime import datetime

from tmdc.tmd_types import (
    DownloadResult,
    UserInfo,
    ListInfo,
    ProxyStatus,
    CookieInfo,
    BatchConfig,
    MenuOption,
    create_logger,
)


class TestDownloadResult:
    """下载结果数据类测试"""

    def test_default_values(self):
        """测试默认值"""
        result = DownloadResult()
        assert result.exit_code == 0
        assert result.warn_count == 0
        assert result.error_count == 0
        assert result.warn_users == []
        assert result.error_messages == []
        assert result.raw_output == ""
        assert result.duration == 0.0
        assert result.target_type == ""
        assert result.target_id == ""

    def test_success_property(self):
        """测试 success 属性"""
        result = DownloadResult()
        assert result.success is True

        result.exit_code = 1
        assert result.success is False

        result.exit_code = 0
        result.error_count = 1
        assert result.success is False

    def test_has_warnings_property(self):
        """测试 has_warnings 属性"""
        result = DownloadResult()
        assert result.has_warnings is False

        result.warn_count = 1
        assert result.has_warnings is True

    def test_has_errors_property(self):
        """测试 has_errors 属性"""
        result = DownloadResult()
        assert result.has_errors is False

        result.exit_code = 1
        assert result.has_errors is True

        result.exit_code = 0
        result.error_count = 1
        assert result.has_errors is True

    def test_get_success_message_user(self):
        """测试用户成功消息"""
        result = DownloadResult(target_type="user", target_id="elonmusk")
        assert "@elonmusk" in result.get_success_message()

    def test_get_success_message_list(self):
        """测试列表成功消息"""
        result = DownloadResult(target_type="list", target_id="123456")
        assert "123456" in result.get_success_message()

    def test_get_success_message_following(self):
        """测试关注列表成功消息"""
        result = DownloadResult(target_type="following", target_id="elonmusk")
        assert "关注列表" in result.get_success_message()

    def test_get_error_message_user(self):
        """测试用户错误消息"""
        result = DownloadResult(target_type="user", target_id="elonmusk")
        assert "@elonmusk" in result.get_error_message()

    def test_get_error_message_list(self):
        """测试列表错误消息"""
        result = DownloadResult(target_type="list", target_id="123456")
        assert "123456" in result.get_error_message()

    def test_get_start_message_user(self):
        """测试用户开始消息"""
        result = DownloadResult(target_type="user", target_id="elonmusk")
        assert "@elonmusk" in result.get_start_message()

    def test_get_start_message_list(self):
        """测试列表开始消息"""
        result = DownloadResult(target_type="list", target_id="123456")
        assert "123456" in result.get_start_message()

    def test_merge_results(self):
        """测试合并结果"""
        result1 = DownloadResult(
            exit_code=1,
            warn_count=2,
            error_count=1,
            warn_users=["user1", "user2"],
            error_messages=["error1"],
            duration=1.5,
        )
        result2 = DownloadResult(
            exit_code=0,
            warn_count=1,
            error_count=2,
            warn_users=["user2", "user3"],
            error_messages=["error2", "error3"],
            duration=2.0,
        )
        merged = result1.merge(result2)
        assert merged.exit_code == 1
        assert merged.warn_count == 3
        assert merged.error_count == 3
        assert len(merged.warn_users) == 3
        assert len(merged.error_messages) == 3
        assert merged.duration == 3.5


class TestUserInfo:
    """用户信息数据类测试"""

    def test_default_values(self):
        """测试默认值"""
        user = UserInfo(screen_name="elonmusk", name="Elon Musk")
        assert user.screen_name == "elonmusk"
        assert user.name == "Elon Musk"
        assert user.entity_id is None
        assert user.latest_release_time is None
        assert user.timestamp is None

    def test_str_representation(self):
        """测试字符串表示"""
        user = UserInfo(screen_name="elonmusk", name="Elon Musk")
        assert "@elonmusk" in str(user)
        assert "Elon Musk" in str(user)

    def test_str_with_timestamp(self):
        """测试带时间戳的字符串表示"""
        ts = datetime(2024, 1, 15)
        user = UserInfo(screen_name="elonmusk", name="Elon Musk", timestamp=ts)
        s = str(user)
        assert "2024-01-15" in s

    def test_str_without_name(self):
        """测试无名称的字符串表示"""
        user = UserInfo(screen_name="elonmusk", name="")
        s = str(user)
        assert "@elonmusk" in s


class TestListInfo:
    """列表信息数据类测试"""

    def test_default_values(self):
        """测试默认值"""
        list_info = ListInfo(list_id=123456)
        assert list_info.list_id == 123456
        assert list_info.name is None
        assert list_info.member_count == 0
        assert list_info.timestamp is None

    def test_str_representation(self):
        """测试字符串表示"""
        list_info = ListInfo(list_id=123456, name="Tech News")
        s = str(list_info)
        assert "123456" in s
        assert "Tech News" in s

    def test_str_with_member_count(self):
        """测试带成员数的字符串表示"""
        list_info = ListInfo(list_id=123456, member_count=100)
        s = str(list_info)
        assert "100" in s
        assert "成员" in s


class TestProxyStatus:
    """代理状态数据类测试"""

    def test_default_values(self):
        """测试默认值"""
        status = ProxyStatus(is_enabled=True)
        assert status.is_enabled is True
        assert status.is_reachable is False
        assert status.hostname == "127.0.0.1"
        assert status.port == 7897

    def test_address_property(self):
        """测试 address 属性"""
        status = ProxyStatus(is_enabled=True, hostname="192.168.1.1", port=8080)
        assert status.address == "192.168.1.1:8080"

    def test_status_text_disabled(self):
        """测试禁用状态文本"""
        status = ProxyStatus(is_enabled=False)
        assert status.status_text == "已禁用"

    def test_status_text_reachable(self):
        """测试可用状态文本"""
        status = ProxyStatus(is_enabled=True, is_reachable=True)
        assert status.status_text == "可用"

    def test_status_text_unreachable(self):
        """测试不可用状态文本"""
        status = ProxyStatus(
            is_enabled=True, is_reachable=False, error_message="Connection refused"
        )
        assert "不可用" in status.status_text
        assert "Connection refused" in status.status_text


class TestCookieInfo:
    """Cookie 信息数据类测试"""

    def test_default_values(self):
        """测试默认值"""
        cookie = CookieInfo(name="auth_token", value="abc123")
        assert cookie.name == "auth_token"
        assert cookie.value == "abc123"
        assert cookie.domain is None
        assert cookie.path == "/"

    def test_is_masked_property(self):
        """测试 is_masked 属性"""
        cookie = CookieInfo(name="auth_token", value="abc123")
        assert cookie.is_masked is False

        cookie = CookieInfo(name="auth_token", value="abc***def")
        assert cookie.is_masked is True

    def test_mask_value_short(self):
        """测试短值脱敏"""
        cookie = CookieInfo(name="auth_token", value="abc")
        masked = cookie.mask_value(visible_chars=4)
        assert masked == "***"

    def test_mask_value_normal(self):
        """测试正常值脱敏"""
        cookie = CookieInfo(name="auth_token", value="abcdefghijklmnop")
        masked = cookie.mask_value(visible_chars=4)
        assert masked == "abcd***"


class TestBatchConfig:
    """批量配置数据类测试"""

    def test_default_values(self):
        """测试默认值"""
        config = BatchConfig()
        assert config.batch_size == 3
        assert config.delay_success_min == 0
        assert config.delay_success_max == 0
        assert config.delay_fail_min == 0
        assert config.delay_fail_max == 0

    def test_is_delay_success_enabled(self):
        """测试成功延迟启用检测"""
        config = BatchConfig()
        assert config.is_delay_success_enabled is False

        config = BatchConfig(delay_success_max=10)
        assert config.is_delay_success_enabled is True

    def test_is_delay_fail_enabled(self):
        """测试失败延迟启用检测"""
        config = BatchConfig()
        assert config.is_delay_fail_enabled is False

        config = BatchConfig(delay_fail_max=10)
        assert config.is_delay_fail_enabled is True


class TestMenuOption:
    """菜单选项数据类测试"""

    def test_default_values(self):
        """测试默认值"""
        option = MenuOption(key="1", name="下载用户")
        assert option.key == "1"
        assert option.name == "下载用户"
        assert option.description == ""
        assert option.handler is None

    def test_with_handler(self):
        """测试带处理函数"""
        called = []

        def handler():
            called.append(True)

        option = MenuOption(key="1", name="测试", handler=handler)
        option.handler()
        assert len(called) == 1


class TestCreateLogger:
    """日志创建函数测试"""

    def test_create_logger_default_name(self):
        """测试默认名称创建日志"""
        logger = create_logger()
        assert logger.name == "TMDController"

    def test_create_logger_custom_name(self):
        """测试自定义名称创建日志"""
        logger = create_logger("TestLogger")
        assert logger.name == "TestLogger"

    def test_logger_has_handler(self):
        """测试日志有处理器"""
        logger = create_logger("TestHandler")
        assert len(logger.handlers) > 0

    def test_logger_level(self):
        """测试日志级别"""
        logger = create_logger("TestLevel")
        assert logger.level == 20
