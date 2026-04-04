# -*- coding: utf-8 -*-
"""时间戳服务测试

测试 TimestampService 的核心功能。
采用智能选择操作方式：已存在实体直接数据库操作，不存在则通过 TMD 创建。
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock

from tmdc.services.timestamp_service import TimestampService
from tmdc.tmd_types import BatchOperationResult


class TestSetSyncTimestamp:
    """测试 set_sync_timestamp 方法"""

    @pytest.fixture
    def mock_services(self):
        config = Mock()
        logger = Mock()
        db_service = Mock()
        dl_service = Mock()
        return config, logger, db_service, dl_service

    def test_calls_database_service_set_user_timestamp(self, mock_services):
        """应该调用 database_service.set_user_timestamp"""
        config, logger, db_service, dl_service = mock_services

        db_service.set_user_timestamp.return_value = (True, "testuser")

        service = TimestampService(
            config=config, logger=logger,
            database_service=db_service, download_service=dl_service,
        )

        result = service.set_sync_timestamp(1, datetime(2024, 1, 1))

        assert result.success is True
        db_service.set_user_timestamp.assert_called_once()
        assert "testuser" in result.message

    def test_returns_failure_when_db_returns_false(self, mock_services):
        """数据库返回失败时返回失败结果"""
        config, logger, db_service, dl_service = mock_services

        db_service.set_user_timestamp.return_value = (False, None)

        service = TimestampService(
            config=config, logger=logger,
            database_service=db_service, download_service=dl_service,
        )

        result = service.set_sync_timestamp(99999, None)

        assert result.success is False
        assert "失败" in result.error

    def test_no_print_output(self, mock_services, capsys):
        """不产生 print 输出"""
        config, logger, db_service, dl_service = mock_services

        db_service.set_user_timestamp.return_value = (False, None)

        service = TimestampService(
            config=config, logger=logger,
            database_service=db_service, download_service=dl_service,
        )

        service.set_sync_timestamp(1, None)

        captured = capsys.readouterr()
        assert captured.out == "", f"服务层不应有 print 输出，实际输出: {captured.out}"


class TestGetOrCreateUserEntity:
    """测试 get_or_create_user_entity 方法"""

    @pytest.fixture
    def mock_services(self):
        config = Mock()
        logger = Mock()
        db_service = Mock()
        dl_service = Mock()
        return config, logger, db_service, dl_service

    def test_existing_user_calls_direct_set(self, mock_services):
        """已存在用户直接调用数据库操作"""
        config, logger, db_service, dl_service = mock_services

        db_service.get_user_entity_info.return_value = {
            "id": 1,
            "screen_name": "testuser",
            "name": "Test",
            "entity_id": 1,
            "latest_release_time": None,
        }
        db_service.set_user_timestamp.return_value = (True, "testuser")

        service = TimestampService(
            config=config, logger=logger,
            database_service=db_service, download_service=dl_service,
        )

        result = service.get_or_create_user_entity("testuser", None)

        assert result.success is True
        db_service.get_user_entity_info.assert_called_once_with("testuser")
        db_service.set_user_timestamp.assert_called_once()
        dl_service.run_tmd.assert_not_called()

    def test_new_user_calls_tmd(self, mock_services):
        """新用户调用 TMD 创建"""
        config, logger, db_service, dl_service = mock_services

        db_service.get_user_entity_info.return_value = None
        dl_service.run_tmd.return_value = (0, "", "")

        def get_entity_after_create(screen_name):
            return {
                "id": 1,
                "screen_name": screen_name,
                "name": "New User",
                "entity_id": 1,
                "latest_release_time": None,
            }

        db_service.get_user_entity_info.side_effect = [
            None,
            get_entity_after_create("newuser"),
        ]

        service = TimestampService(
            config=config, logger=logger,
            database_service=db_service, download_service=dl_service,
        )

        result = service.get_or_create_user_entity("newuser", None)

        assert result.success is True
        dl_service.run_tmd.assert_called_once()

    def test_new_user_without_download_service_returns_error(self, mock_services):
        """新用户但无 download_service 时返回错误"""
        config, logger, db_service, _ = mock_services

        db_service.get_user_entity_info.return_value = None

        service = TimestampService(
            config=config, logger=logger,
            database_service=db_service, download_service=None,
        )

        result = service.get_or_create_user_entity("newuser", None)

        assert result.success is False
        assert "不存在" in result.error


class TestGetOrCreateListEntity:
    """测试 get_or_create_list_entity 方法"""

    @pytest.fixture
    def mock_services(self):
        config = Mock()
        logger = Mock()
        db_service = Mock()
        dl_service = Mock()
        return config, logger, db_service, dl_service

    def test_existing_list_calls_direct_set(self, mock_services):
        """已存在列表直接调用数据库操作"""
        config, logger, db_service, dl_service = mock_services

        db_service.check_list_entity_exists.return_value = True
        db_service.set_list_timestamp.return_value = True

        service = TimestampService(
            config=config, logger=logger,
            database_service=db_service, download_service=dl_service,
        )

        result = service.get_or_create_list_entity(123456, None)

        assert result.success is True
        db_service.check_list_entity_exists.assert_called_once_with(123456)
        db_service.set_list_timestamp.assert_called_once()
        dl_service.run_tmd.assert_not_called()

    def test_new_list_calls_tmd(self, mock_services):
        """新列表调用 TMD 创建"""
        config, logger, db_service, dl_service = mock_services

        db_service.check_list_entity_exists.side_effect = [False, True]
        dl_service.run_tmd.return_value = (0, "", "")

        service = TimestampService(
            config=config, logger=logger,
            database_service=db_service, download_service=dl_service,
        )

        result = service.get_or_create_list_entity(123456, None)

        assert result.success is True
        dl_service.run_tmd.assert_called_once()


class TestBatchSetListTimestamp:
    """测试 batch_set_list_timestamp 方法"""

    @pytest.fixture
    def mock_services(self):
        config = Mock()
        logger = Mock()
        db_service = Mock()
        dl_service = Mock()
        return config, logger, db_service, dl_service

    def test_returns_batch_operation_result_type(self, mock_services):
        """返回值类型必须是 BatchOperationResult"""
        config, logger, db_service, dl_service = mock_services

        dl_service.run_tmd.return_value = (0, "", "")

        service = TimestampService(
            config=config, logger=logger,
            database_service=db_service, download_service=dl_service,
        )

        result = service.batch_set_list_timestamp(123, None)

        assert isinstance(result, BatchOperationResult)

    def test_calls_tmd_with_list_arg(self, mock_services):
        """应该调用 TMD --list --mark-downloaded"""
        config, logger, db_service, dl_service = mock_services

        dl_service.run_tmd.return_value = (0, "", "")

        service = TimestampService(
            config=config, logger=logger,
            database_service=db_service, download_service=dl_service,
        )

        result = service.batch_set_list_timestamp(123456, datetime(2024, 1, 1))

        assert result.success is True
        dl_service.run_tmd.assert_called_once()
        args = dl_service.run_tmd.call_args[1]["args"]
        assert "-list" in args
        assert "123456" in args
        assert "-mark-downloaded" in args

    def test_tmd_failure_returns_failure(self, mock_services):
        """TMD 失败时返回失败结果"""
        config, logger, db_service, dl_service = mock_services

        dl_service.run_tmd.return_value = (1, "", "list not found")

        service = TimestampService(
            config=config, logger=logger,
            database_service=db_service, download_service=dl_service,
        )

        result = service.batch_set_list_timestamp(99999, None)

        assert result.success is False
        assert "not found" in result.error.lower() or result.error != ""

    def test_parses_tmd_output_correctly(self, mock_services):
        """正确解析 TMD 输出"""
        config, logger, db_service, dl_service = mock_services

        tmd_output = """
=== MARK_DOWNLOADED_RESULTS ===
ENTITY_ID:1|USER_ID:44196397|SCREEN_NAME:elonmusk|STATUS:OK
ENTITY_ID:2|USER_ID:23248887|SCREEN_NAME:NASA|STATUS:OK
ENTITY_ID:3|USER_ID:12345|SCREEN_NAME:testuser|STATUS:FAIL
=== END_RESULTS ===
"""
        dl_service.run_tmd.return_value = (0, tmd_output, "")

        service = TimestampService(
            config=config, logger=logger,
            database_service=db_service, download_service=dl_service,
        )

        result = service.batch_set_list_timestamp(123, None)

        assert result.success is True
        assert result.success_count == 2
        assert result.failed_count == 1
        assert "testuser" in result.failed_items

    def test_returns_failure_without_download_service(self, mock_services):
        """无 download_service 时返回失败"""
        config, logger, db_service, _ = mock_services

        service = TimestampService(
            config=config, logger=logger,
            database_service=db_service, download_service=None,
        )

        result = service.batch_set_list_timestamp(123, None)

        assert result.success is False
        assert "不可用" in result.error


class TestFormatTimestampDisplay:
    """测试 format_timestamp_display 方法"""

    @pytest.fixture
    def service(self):
        config = Mock()
        logger = Mock()
        db_service = Mock()
        dl_service = Mock()
        return TimestampService(
            config=config,
            logger=logger,
            database_service=db_service,
            download_service=dl_service,
        )

    def test_returns_default_for_none(self, service):
        """None 返回默认文本"""
        result = service.format_timestamp_display(None)
        assert result == "从未同步"

    def test_returns_default_for_empty_string(self, service):
        """空字符串返回默认文本"""
        result = service.format_timestamp_display("")
        assert result == "从未同步"

    def test_returns_string_representation(self, service):
        """返回字符串表示"""
        timestamp = datetime(2024, 1, 15, 10, 30, 0)
        result = service.format_timestamp_display(timestamp)
        assert "2024" in result or "01" in result or "15" in result


class TestFormatDuration:
    """测试 format_duration 方法"""

    @pytest.fixture
    def service(self):
        config = Mock()
        logger = Mock()
        db_service = Mock()
        dl_service = Mock()
        return TimestampService(
            config=config,
            logger=logger,
            database_service=db_service,
            download_service=dl_service,
        )

    def test_returns_formatted_duration(self, service):
        """返回格式化的时间间隔"""
        td = timedelta(days=7, hours=12, minutes=30)
        result = service.format_duration(td)
        assert isinstance(result, str)
        assert len(result) > 0
