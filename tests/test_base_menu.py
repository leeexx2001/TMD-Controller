# -*- coding: utf-8 -*-
"""
BaseMenu 单元测试
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from tmdc.menus.base_menu import BaseMenu

if TYPE_CHECKING:
    pass


class DummyMenu(BaseMenu):
    """用于测试的虚拟菜单类"""

    def show(self) -> None:
        pass


class TestBaseMenuNewMethods:
    """测试 BaseMenu 新增方法"""

    @pytest.fixture
    def menu(self):
        """提供带有 mock UI 的 DummyMenu 实例"""
        ui = MagicMock()
        logger = MagicMock()
        config = MagicMock()
        return DummyMenu(ui, logger, config)

    def test_get_menu_choice_normal(self, menu):
        """测试正常菜单选择获取"""
        menu.ui.safe_input.return_value = "1"
        result = menu._get_menu_choice()
        assert result == "1"
        menu.ui.safe_input.assert_called_once()

    def test_get_menu_choice_with_whitespace(self, menu):
        """测试带空白的输入"""
        menu.ui.safe_input.return_value = "  1  "
        result = menu._get_menu_choice()
        assert result == "1"

    def test_get_menu_choice_lowercase(self, menu):
        """测试小写输入转大写"""
        menu.ui.safe_input.return_value = "a"
        result = menu._get_menu_choice()
        assert result == "A"

    def test_get_menu_choice_empty(self, menu):
        """测试空输入"""
        menu.ui.safe_input.return_value = ""
        result = menu._get_menu_choice()
        assert result == ""

    def test_get_menu_choice_none(self, menu):
        """测试 None 输入（如 Ctrl+C）"""
        menu.ui.safe_input.return_value = None
        result = menu._get_menu_choice()
        assert result == ""

    def test_show_result_success(self, menu, capsys):
        """测试显示成功结果"""
        menu._show_result(True, "成功消息")
        captured = capsys.readouterr()
        assert "✅" in captured.out
        assert "成功消息" in captured.out

    def test_show_result_failure(self, menu, capsys):
        """测试显示失败结果"""
        menu._show_result(False, "失败消息")
        captured = capsys.readouterr()
        assert "❌" in captured.out
        assert "失败消息" in captured.out

    def test_show_result_with_details(self, menu, capsys):
        """测试显示带详情的成功结果"""
        menu._show_result(True, "成功", ["详情1", "详情2"])
        captured = capsys.readouterr()
        assert "详情1" in captured.out
        assert "详情2" in captured.out

    def test_confirm_dangerous_success(self, menu):
        """测试危险操作确认成功"""
        menu.ui.safe_input.return_value = "DELETE"
        result = menu._confirm_dangerous("删除数据", "DELETE")
        assert result is True

    def test_confirm_dangerous_cancel(self, menu):
        """测试危险操作确认取消"""
        menu.ui.safe_input.return_value = ""
        result = menu._confirm_dangerous("删除数据", "DELETE")
        assert result is False

    def test_confirm_dangerous_wrong_text(self, menu):
        """测试危险操作确认输入错误文本"""
        menu.ui.safe_input.return_value = "WRONG"
        result = menu._confirm_dangerous("删除数据", "DELETE")
        assert result is False

    def test_confirm_dangerous_case_insensitive(self, menu):
        """测试危险操作确认大小写不敏感"""
        menu.ui.safe_input.return_value = "delete"
        result = menu._confirm_dangerous("删除数据", "DELETE")
        assert result is True

    def test_get_choice_index_valid(self, menu):
        """测试有效序号选择"""
        menu.ui.safe_input.return_value = "2"
        result = menu._get_choice_index(5)
        assert result == 1  # 0-based

    def test_get_choice_index_first(self, menu):
        """测试第一个序号"""
        menu.ui.safe_input.return_value = "1"
        result = menu._get_choice_index(5)
        assert result == 0

    def test_get_choice_index_last(self, menu):
        """测试最后一个序号"""
        menu.ui.safe_input.return_value = "5"
        result = menu._get_choice_index(5)
        assert result == 4

    def test_get_choice_index_empty(self, menu):
        """测试空输入"""
        menu.ui.safe_input.return_value = ""
        result = menu._get_choice_index(5)
        assert result is None

    def test_get_choice_index_none(self, menu):
        """测试 None 输入"""
        menu.ui.safe_input.return_value = None
        result = menu._get_choice_index(5)
        assert result is None

    def test_get_choice_index_non_digit(self, menu):
        """测试非数字输入"""
        menu.ui.safe_input.return_value = "abc"
        result = menu._get_choice_index(5)
        assert result is None

    def test_get_choice_index_out_of_range_high(self, menu):
        """测试超出范围的序号（太大）"""
        menu.ui.safe_input.return_value = "10"
        result = menu._get_choice_index(5)
        assert result is None
        menu.ui.pause.assert_called_once()

    def test_get_choice_index_out_of_range_low(self, menu):
        """测试超出范围的序号（0）"""
        menu.ui.safe_input.return_value = "0"
        result = menu._get_choice_index(5)
        assert result is None
        menu.ui.pause.assert_called_once()

    def test_get_choice_index_zero_max(self, menu):
        """测试最大值为0的情况"""
        menu.ui.safe_input.return_value = "1"
        result = menu._get_choice_index(0)
        assert result is None


class TestBaseMenuRunMenuLoop:
    """测试 _run_menu_loop 方法"""

    @pytest.fixture
    def menu(self):
        ui = MagicMock()
        logger = MagicMock()
        config = MagicMock()
        return DummyMenu(ui, logger, config)

    def test_run_menu_loop_exit(self, menu):
        """测试菜单循环退出"""
        menu.ui.safe_input.return_value = "0"
        handler = MagicMock()

        menu._run_menu_loop(
            title="测试",
            options=[("1", "选项", "")],
            handlers={"1": handler},
        )

        handler.assert_not_called()

    def test_run_menu_loop_handler_called(self, menu):
        """测试菜单处理器被调用"""
        menu.ui.safe_input.side_effect = ["1", "0"]
        handler = MagicMock()

        menu._run_menu_loop(
            title="测试",
            options=[("1", "选项", "")],
            handlers={"1": handler},
        )

        handler.assert_called_once()

    def test_run_menu_loop_invalid_choice(self, menu):
        """测试无效选择不调用处理器"""
        menu.ui.safe_input.side_effect = ["X", "0"]
        handler = MagicMock()

        menu._run_menu_loop(
            title="测试",
            options=[("1", "选项", "")],
            handlers={"1": handler},
        )

        handler.assert_not_called()

    def test_run_menu_loop_with_status(self, menu):
        """测试带状态行的菜单循环"""
        menu.ui.safe_input.side_effect = ["0"]

        menu._run_menu_loop(
            title="测试",
            options=[("1", "选项", "")],
            handlers={},
            status_lines=[("状态", "值", "")],
        )

        # 验证 renderer 被调用
        assert menu._renderer is not None

    def test_run_menu_loop_with_hints(self, menu):
        """测试带提示的菜单循环"""
        menu.ui.safe_input.side_effect = ["0"]

        menu._run_menu_loop(
            title="测试",
            options=[("1", "选项", "")],
            handlers={},
            hints=["提示1"],
        )

        assert menu._renderer is not None

    def test_run_menu_loop_custom_exit_key(self, menu):
        """测试自定义退出键"""
        menu.ui.safe_input.side_effect = ["Q"]
        handler = MagicMock()

        menu._run_menu_loop(
            title="测试",
            options=[("1", "选项", "")],
            handlers={"1": handler},
            exit_key="Q",
        )

        handler.assert_not_called()
