# -*- coding: utf-8 -*-
"""CLI 时间戳处理测试"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from tmdc.cli.cli_handler import CLIHandler
from tmdc.tmd_types import OperationResult, BatchOperationResult


class TestHandleUserTimestamp:
    """测试 _handle_user_timestamp 方法"""

    @pytest.fixture
    def mock_container(self):
        container = Mock()
        container.config = Mock()
        container.logger = Mock()
        container.database_service = Mock()
        container.timestamp_service = Mock()
        container.ui = Mock()
        container.ui.headless_mode = False
        return container

    def test_auto_creates_nonexistent_user(self, mock_container):
        """自动创建不存在的用户"""
        mock_container.database_service.find_users_for_reset.return_value = []
        mock_container.timestamp_service.get_or_create_user_entity.return_value = OperationResult(
            success=True, message="已创建用户", data={"screen_name": "testuser"}
        )

        handler = CLIHandler(mock_container)
        result = handler._handle_user_timestamp(
            "testuser",
            None,
            "全量下载",
            mock_container.database_service,
            mock_container.timestamp_service,
        )

        assert result == 0
        mock_container.timestamp_service.get_or_create_user_entity.assert_called_once()

    def test_returns_failure_on_create_error(self, mock_container):
        """创建失败时返回错误"""
        mock_container.database_service.find_users_for_reset.return_value = []
        mock_container.timestamp_service.get_or_create_user_entity.return_value = OperationResult(
            success=False, error="创建失败"
        )

        handler = CLIHandler(mock_container)
        result = handler._handle_user_timestamp(
            "testuser",
            None,
            "全量下载",
            mock_container.database_service,
            mock_container.timestamp_service,
        )

        assert result == 1


class TestHandleListTimestamp:
    """测试 _handle_list_timestamp 方法"""

    @pytest.fixture
    def mock_container(self):
        container = Mock()
        container.config = Mock()
        container.logger = Mock()
        container.database_service = Mock()
        container.timestamp_service = Mock()
        container.ui = Mock()
        container.ui.headless_mode = False
        return container

    def test_auto_creates_nonexistent_list(self, mock_container):
        """自动创建不存在的列表"""
        mock_container.database_service.check_list_exists.return_value = False
        mock_container.timestamp_service.get_or_create_list_entity.return_value = OperationResult(
            success=True, message="已创建列表"
        )

        handler = CLIHandler(mock_container)
        result = handler._handle_list_timestamp(
            "123456789",
            None,
            "全量下载",
            False,
            mock_container.database_service,
            mock_container.timestamp_service,
        )

        assert result == 0
        mock_container.timestamp_service.get_or_create_list_entity.assert_called_once_with(
            123456789, None
        )

    def test_returns_failure_on_list_create_error(self, mock_container):
        """列表创建失败时返回错误"""
        mock_container.database_service.check_list_exists.return_value = False
        mock_container.timestamp_service.get_or_create_list_entity.return_value = OperationResult(
            success=False, error="创建失败"
        )

        handler = CLIHandler(mock_container)
        result = handler._handle_list_timestamp(
            "123456789",
            None,
            "全量下载",
            False,
            mock_container.database_service,
            mock_container.timestamp_service,
        )

        assert result == 1

    def test_batch_set_returns_correct_exit_code(self, mock_container):
        """批量设置返回正确的退出码"""
        mock_container.database_service.check_list_exists.return_value = True
        mock_container.timestamp_service.batch_set_list_timestamp.return_value = (
            BatchOperationResult(
                success=True,
                message="成功处理 5/5 个用户",
                total=5,
                success_count=5,
                failed_count=0,
            )
        )

        handler = CLIHandler(mock_container)
        result = handler._handle_list_timestamp(
            "123456789",
            None,
            "全量下载",
            True,
            mock_container.database_service,
            mock_container.timestamp_service,
        )

        assert result == 0

    def test_batch_set_all_failed_returns_error(self, mock_container):
        """批量设置全部失败时返回错误"""
        mock_container.database_service.check_list_exists.return_value = True
        mock_container.timestamp_service.batch_set_list_timestamp.return_value = (
            BatchOperationResult(
                success=False,
                error="全部 5 个用户处理失败",
                total=5,
                success_count=0,
                failed_count=5,
                failed_items=["user1", "user2", "user3", "user4", "user5"],
            )
        )

        handler = CLIHandler(mock_container)
        result = handler._handle_list_timestamp(
            "123456789",
            None,
            "全量下载",
            True,
            mock_container.database_service,
            mock_container.timestamp_service,
        )

        assert result == 1


class TestEnsureUserExistsNotCalled:
    """验证不再调用 _ensure_user_exists"""

    def test_no_call_to_private_method(self):
        """不调用 _ensure_user_exists 私有方法"""
        from tmdc.cli import cli_handler
        import inspect

        assert not hasattr(
            cli_handler.CLIHandler, "_ensure_user_exists"
        ), "CLIHandler 不应有 _ensure_user_exists 方法"
