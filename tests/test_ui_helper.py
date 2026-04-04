# -*- coding: utf-8 -*-
"""测试 ui_helper.py"""

import pytest
from unittest.mock import patch, MagicMock

from tmdc.ui.ui_helper import UIHelper


class TestUIHelperInit:
    """UIHelper 初始化测试"""

    def test_default_init(self):
        """测试默认初始化"""
        ui = UIHelper()
        assert ui.headless_mode is False

    def test_headless_mode(self):
        """测试无头模式"""
        ui = UIHelper(headless_mode=True)
        assert ui.headless_mode is True


class TestUIHelperProperties:
    """UIHelper 属性测试"""

    def test_ui_width(self):
        """测试 UI 宽度"""
        ui = UIHelper()
        assert ui.UI_WIDTH == 62

    def test_separator_line(self):
        """测试分隔线"""
        ui = UIHelper()
        assert len(ui.SEPARATOR_LINE) == 62
        assert ui.SEPARATOR_LINE == "-" * 62

    def test_header_separator(self):
        """测试标题分隔线"""
        ui = UIHelper()
        assert len(ui.HEADER_SEPARATOR) == 62
        assert ui.HEADER_SEPARATOR == "=" * 62

    def test_icons(self):
        """测试图标"""
        ui = UIHelper()
        assert ui.ICON_USER == "👤"
        assert ui.ICON_LIST == "📋"
        assert ui.ICON_COOKIE == "🍪"


class TestShowHeader:
    """标题显示测试"""

    def test_show_header_title_only(self, capsys):
        """测试仅显示主标题"""
        ui = UIHelper()
        ui.show_header("主菜单")
        captured = capsys.readouterr()
        assert "主菜单" in captured.out
        assert "=" * 60 in captured.out

    def test_show_header_with_subtitle(self, capsys):
        """测试显示主标题和副标题"""
        ui = UIHelper()
        ui.show_header("主菜单", "v7.0.0")
        captured = capsys.readouterr()
        assert "主菜单" in captured.out
        assert "v7.0.0" in captured.out


class TestPrintMethods:
    """打印方法测试"""

    def test_print_success(self, capsys):
        """测试成功消息"""
        ui = UIHelper()
        ui.print_success("操作成功")
        captured = capsys.readouterr()
        assert "操作成功" in captured.out

    def test_print_error(self, capsys):
        """测试错误消息"""
        ui = UIHelper()
        ui.print_error("操作失败")
        captured = capsys.readouterr()
        assert "操作失败" in captured.out

    def test_print_warning(self, capsys):
        """测试警告消息"""
        ui = UIHelper()
        ui.print_warning("警告信息")
        captured = capsys.readouterr()
        assert "警告信息" in captured.out

    def test_print_info(self, capsys):
        """测试信息消息"""
        ui = UIHelper()
        ui.print_info("提示信息")
        captured = capsys.readouterr()
        assert "提示信息" in captured.out

    def test_print_separator(self, capsys):
        """测试分隔线"""
        ui = UIHelper()
        ui.print_separator()
        captured = capsys.readouterr()
        assert "-" * 60 in captured.out


class TestShowListWarning:
    """列表警告显示测试"""

    def test_show_list_warning_basic(self, capsys):
        """测试基本列表警告"""
        ui = UIHelper()
        ui.show_list_warning("1234567890")
        captured = capsys.readouterr()
        assert "1234567890" in captured.out
        assert "大型列表" in captured.out

    def test_show_list_warning_with_hint(self, capsys):
        """测试带高级参数提示的列表警告"""
        ui = UIHelper(headless_mode=True)
        ui.show_list_warning("1234567890", show_advanced_hint=True)
        captured = capsys.readouterr()
        assert "高级参数" in captured.out


class TestShowBatchSummary:
    """批量摘要显示测试"""

    def test_show_batch_summary_success_only(self, capsys):
        """测试仅成功的摘要"""
        ui = UIHelper()
        ui.show_batch_summary(total=10, success=10, failed=0)
        captured = capsys.readouterr()
        assert "总数: 10" in captured.out
        assert "成功: 10" in captured.out
        assert "失败: 0" in captured.out

    def test_show_batch_summary_with_failures(self, capsys):
        """测试带失败的摘要"""
        ui = UIHelper()
        ui.show_batch_summary(total=10, success=7, failed=3)
        captured = capsys.readouterr()
        assert "失败: 3" in captured.out

    def test_show_batch_summary_with_failed_items(self, capsys):
        """测试带失败项目的摘要"""
        ui = UIHelper()
        failed_items = ["user1", "user2", "user3"]
        ui.show_batch_summary(total=10, success=7, failed=3, failed_items=failed_items)
        captured = capsys.readouterr()
        assert "失败项目列表" in captured.out
        assert "user1" in captured.out

    def test_show_batch_summary_many_failed_items(self, capsys):
        """测试大量失败项目的摘要"""
        ui = UIHelper()
        failed_items = [f"user{i}" for i in range(15)]
        ui.show_batch_summary(total=20, success=5, failed=15, failed_items=failed_items)
        captured = capsys.readouterr()
        assert "还有 5 个失败项目" in captured.out


class TestConfirmAction:
    """确认操作测试"""

    def test_confirm_action_headless_non_explicit(self):
        """测试无头模式非显式确认"""
        ui = UIHelper(headless_mode=True)
        result = ui.confirm_action("确认?", explicit=False, default=True)
        assert result is True

    def test_confirm_action_headless_explicit(self, capsys):
        """测试无头模式显式确认"""
        ui = UIHelper(headless_mode=True)
        result = ui.confirm_action("确认?", explicit=True)
        assert result is False
        captured = capsys.readouterr()
        assert "Headless" in captured.out

    @patch("builtins.input", return_value="")
    def test_confirm_action_non_explicit_default(self, mock_input):
        """测试非显式确认默认行为"""
        ui = UIHelper()
        result = ui.confirm_action("确认?", explicit=False)
        assert result is True

    @patch("builtins.input", return_value="N")
    def test_confirm_action_cancel(self, mock_input, capsys):
        """测试取消确认"""
        ui = UIHelper()
        result = ui.confirm_action("确认?", explicit=False)
        assert result is False


class TestConfirmYesNo:
    """是/否确认测试"""

    @patch("builtins.input", return_value="Y")
    def test_confirm_yes_no_yes(self, mock_input):
        """测试确认是"""
        ui = UIHelper()
        result = ui.confirm_yes_no("是否继续?")
        assert result is True

    @patch("builtins.input", return_value="N")
    def test_confirm_yes_no_no(self, mock_input):
        """测试确认否"""
        ui = UIHelper()
        result = ui.confirm_yes_no("是否继续?")
        assert result is False

    @patch("builtins.input", return_value="")
    def test_confirm_yes_no_default_true(self, mock_input):
        """测试默认值为真"""
        ui = UIHelper()
        result = ui.confirm_yes_no("是否继续?", default=True)
        assert result is True

    @patch("builtins.input", return_value="")
    def test_confirm_yes_no_default_false(self, mock_input):
        """测试默认值为假"""
        ui = UIHelper()
        result = ui.confirm_yes_no("是否继续?", default=False)
        assert result is False

    @patch("builtins.input", return_value="invalid")
    def test_confirm_yes_no_invalid(self, mock_input, capsys):
        """测试无效输入"""
        ui = UIHelper()
        result = ui.confirm_yes_no("是否继续?", default=False)
        assert result is False
        captured = capsys.readouterr()
        assert "无效输入" in captured.out


class TestInputNumber:
    """数字输入测试"""

    @patch("builtins.input", return_value="5")
    def test_input_number_valid(self, mock_input):
        """测试有效数字输入"""
        ui = UIHelper()
        result = ui.input_number("请输入数字: ")
        assert result == 5

    @patch("builtins.input", return_value="")
    def test_input_number_empty_with_default(self, mock_input):
        """测试空输入使用默认值"""
        ui = UIHelper()
        result = ui.input_number("请输入数字: ", default=10)
        assert result == 10

    @patch("builtins.input", return_value="")
    def test_input_number_empty_no_default(self, mock_input):
        """测试空输入无默认值"""
        ui = UIHelper()
        result = ui.input_number("请输入数字: ")
        assert result is None

    @patch("builtins.input", return_value="abc")
    def test_input_number_invalid(self, mock_input, capsys):
        """测试无效数字输入"""
        ui = UIHelper()
        result = ui.input_number("请输入数字: ")
        assert result is None
        captured = capsys.readouterr()
        assert "无效输入" in captured.out

    @patch("builtins.input", return_value="5")
    def test_input_number_min_val(self, mock_input, capsys):
        """测试最小值验证"""
        ui = UIHelper()
        result = ui.input_number("请输入数字: ", min_val=10)
        assert result is None
        captured = capsys.readouterr()
        assert "不能小于" in captured.out

    @patch("builtins.input", return_value="100")
    def test_input_number_max_val(self, mock_input, capsys):
        """测试最大值验证"""
        ui = UIHelper()
        result = ui.input_number("请输入数字: ", max_val=10)
        assert result is None
        captured = capsys.readouterr()
        assert "不能大于" in captured.out


class TestSafeInput:
    """安全输入测试"""

    @patch("builtins.input", return_value="test")
    def test_safe_input_valid(self, mock_input):
        """测试有效输入"""
        ui = UIHelper()
        result = ui.safe_input("请输入: ")
        assert result == "test"

    @patch("builtins.input", return_value="")
    def test_safe_input_empty_not_allowed(self, mock_input):
        """测试不允许空输入"""
        ui = UIHelper()
        result = ui.safe_input("请输入: ", allow_empty=False, default="default")
        assert result == "default"

    @patch("builtins.input", return_value="")
    def test_safe_input_empty_allowed(self, mock_input):
        """测试允许空输入"""
        ui = UIHelper()
        result = ui.safe_input("请输入: ", allow_empty=True)
        assert result == ""


class TestPause:
    """暂停测试"""

    def test_pause_headless(self):
        """测试无头模式暂停"""
        ui = UIHelper(headless_mode=True)
        ui.pause("按回车继续...")
