# -*- coding: utf-8 -*-
"""CLI 删除用户项目功能测试"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from argparse import Namespace

from tmdc.cli.cli_handler import CLIHandler


class TestHandleDeleteUser:
    """测试 handle_delete_user 方法"""

    @pytest.fixture
    def mock_container(self):
        container = Mock()
        container.config = Mock()
        container.logger = Mock()
        container.database_service = Mock()
        container.ui = Mock()
        container.ui.headless_mode = False
        return container

    @pytest.fixture
    def handler(self, mock_container):
        return CLIHandler(mock_container)

    def test_database_unavailable_returns_error(self, handler, mock_container):
        """数据库不可用时返回错误"""
        mock_container.database_service.is_database_available.return_value = False
        mock_container.database_service.get_database_unavailable_message.return_value = "DB not found"

        args = Namespace(delete_user="testuser")
        result = handler.handle_delete_user(args)

        assert result == 1

    def test_empty_target_returns_error(self, handler, mock_container):
        """空目标返回错误"""
        mock_container.database_service.is_database_available.return_value = True

        args = Namespace(delete_user="   ")
        result = handler.handle_delete_user(args)

        assert result == 1

    def test_numeric_id_not_found(self, handler, mock_container):
        """数字ID不存在时返回错误"""
        mock_container.database_service.is_database_available.return_value = True
        mock_container.database_service.db_session.return_value.__enter__ = Mock(
            return_value=Mock(fetchone=Mock(return_value=None))
        )
        mock_container.database_service.db_session.return_value.__exit__ = Mock(return_value=False)
        mock_container.database_service.delete_user_project.return_value = (
            False, "用户 ID 12345 不存在于数据库中", {"links": 0, "entities": 0, "names": 0, "users": 0}
        )

        args = Namespace(delete_user="12345")

        with patch('builtins.input', return_value='DELETE'):
            result = handler.handle_delete_user(args)

        assert result == 1

    def test_username_not_found(self, handler, mock_container):
        """用户名不存在时返回错误"""
        mock_container.database_service.is_database_available.return_value = True
        mock_container.database_service.find_users.return_value = []

        args = Namespace(delete_user="nonexistent")
        result = handler.handle_delete_user(args)

        assert result == 1
        mock_container.database_service.find_users.assert_called_once()

    def test_multiple_matches_shows_list(self, handler, mock_container):
        """多个匹配时显示列表并要求精确输入"""
        mock_container.database_service.is_database_available.return_value = True
        mock_container.database_service.find_users.return_value = [
            {"id": 1, "screen_name": "testuser", "name": "Test User"},
            {"id": 2, "screen_name": "testuser2", "name": "Test User 2"},
        ]

        args = Namespace(delete_user="test")
        result = handler.handle_delete_user(args)

        assert result == 1

    def test_headless_mode_rejects(self, handler, mock_container):
        """无头模式自动拒绝"""
        mock_container.database_service.is_database_available.return_value = True
        mock_container.database_service.find_users.return_value = [
            {"id": 12345, "screen_name": "testuser", "name": "Test User"}
        ]
        mock_container.database_service.get_user_entity_info.return_value = None
        mock_container.ui.headless_mode = True

        args = Namespace(delete_user="testuser")
        result = handler.handle_delete_user(args)

        assert result == 1

    def test_cancel_on_wrong_confirm(self, handler, mock_container):
        """确认失败时取消"""
        mock_container.database_service.is_database_available.return_value = True
        mock_container.database_service.find_users.return_value = [
            {"id": 12345, "screen_name": "testuser", "name": "Test User"}
        ]
        mock_container.database_service.get_user_entity_info.return_value = None

        args = Namespace(delete_user="testuser")

        with patch('builtins.input', return_value='no'):
            result = handler.handle_delete_user(args)

        assert result == 130

    def test_successful_delete(self, handler, mock_container):
        """成功删除"""
        mock_container.database_service.is_database_available.return_value = True
        mock_container.database_service.find_users.return_value = [
            {"id": 12345, "screen_name": "testuser", "name": "Test User"}
        ]
        mock_container.database_service.get_user_entity_info.return_value = {
            "screen_name": "testuser",
            "entity_id": 1
        }
        mock_container.database_service.delete_user_project.return_value = (
            True,
            "已删除用户项目，共清理 4 条记录",
            {"links": 1, "entities": 1, "names": 1, "users": 1}
        )

        args = Namespace(delete_user="testuser")

        with patch('builtins.input', return_value='DELETE'):
            result = handler.handle_delete_user(args)

        assert result == 0
        mock_container.database_service.delete_user_project.assert_called_once_with(12345)
        mock_container.logger.info.assert_called_once()

    def test_delete_by_numeric_id(self, handler, mock_container):
        """通过数字ID删除"""
        mock_container.database_service.is_database_available.return_value = True
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = {"screen_name": "testuser"}
        mock_container.database_service.db_session.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_container.database_service.db_session.return_value.__exit__ = Mock(return_value=False)
        mock_container.database_service.delete_user_project.return_value = (
            True,
            "已删除用户项目，共清理 2 条记录",
            {"links": 0, "entities": 0, "names": 0, "users": 1}
        )

        args = Namespace(delete_user="12345")

        with patch('builtins.input', return_value='DELETE'):
            result = handler.handle_delete_user(args)

        assert result == 0
        mock_container.database_service.delete_user_project.assert_called_once_with(12345)

    def test_keyboard_interrupt(self, handler, mock_container):
        """键盘中断处理"""
        mock_container.database_service.is_database_available.return_value = True
        mock_container.database_service.find_users.return_value = [
            {"id": 12345, "screen_name": "testuser", "name": "Test User"}
        ]
        mock_container.database_service.get_user_entity_info.return_value = None

        args = Namespace(delete_user="testuser")

        with patch('builtins.input', side_effect=KeyboardInterrupt()):
            result = handler.handle_delete_user(args)

        assert result == 130

    def test_delete_failure(self, handler, mock_container):
        """删除操作失败"""
        mock_container.database_service.is_database_available.return_value = True
        mock_container.database_service.find_users.return_value = [
            {"id": 12345, "screen_name": "testuser", "name": "Test User"}
        ]
        mock_container.database_service.get_user_entity_info.return_value = None
        mock_container.database_service.delete_user_project.return_value = (
            False,
            "数据库操作失败: connection error",
            {"links": 0, "entities": 0, "names": 0, "users": 0}
        )

        args = Namespace(delete_user="testuser")

        with patch('builtins.input', return_value='DELETE'):
            result = handler.handle_delete_user(args)

        assert result == 1


class TestDeleteUserArgParser:
    """测试参数解析器包含 --delete-user"""

    @pytest.fixture
    def handler(self):
        container = Mock()
        container.config = Mock()
        container.logger = Mock()
        container.database_service = Mock()
        return CLIHandler(container)

    def test_parser_has_delete_user_option(self, handler):
        """解析器包含 --delete-user 选项"""
        parser = handler.create_parser()
        args = parser.parse_args(['--delete-user', 'testuser'])
        assert args.delete_user == 'testuser'

    def test_parser_accepts_numeric_id(self, handler):
        """解析器接受数字ID"""
        parser = handler.create_parser()
        args = parser.parse_args(['--delete-user', '12345'])
        assert args.delete_user == '12345'
