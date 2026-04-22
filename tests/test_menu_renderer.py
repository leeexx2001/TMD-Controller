# -*- coding: utf-8 -*-
"""
MenuRenderer 单元测试
"""

from __future__ import annotations

import pytest

from tmdc.ui.menu_renderer import MenuRenderer
from tmdc.ui.ui_helper import UIHelper


class TestMenuRenderer:
    """测试 MenuRenderer 的渲染功能"""

    @pytest.fixture
    def renderer(self):
        """提供 MenuRenderer 实例"""
        return MenuRenderer(UIHelper())

    def test_render_menu_basic(self, renderer, capsys):
        """测试基本菜单渲染"""
        renderer.render_menu(
            title="测试菜单",
            options=[("1", "选项1", "描述1"), ("0", "返回", "")],
        )
        captured = capsys.readouterr()
        assert "测试菜单" in captured.out
        assert "[1] 选项1" in captured.out
        assert "→ 描述1" in captured.out
        assert "[0] 返回" in captured.out

    def test_render_menu_with_status(self, renderer, capsys):
        """测试带状态行的菜单渲染"""
        renderer.render_menu(
            title="测试菜单",
            options=[("1", "选项1", "描述1")],
            status_lines=[("状态1", "值1", "✅"), ("状态2", "值2", "")],
        )
        captured = capsys.readouterr()
        assert "状态1" in captured.out
        assert "值1" in captured.out
        assert "✅" in captured.out
        assert "状态2" in captured.out
        assert "值2" in captured.out

    def test_render_menu_with_hints(self, renderer, capsys):
        """测试带提示的菜单渲染"""
        renderer.render_menu(
            title="测试菜单",
            options=[("1", "选项1", "描述1")],
            hints=["提示1", "提示2"],
        )
        captured = capsys.readouterr()
        assert "💡 提示1" in captured.out
        assert "💡 提示2" in captured.out

    def test_render_status_line(self, renderer, capsys):
        """测试状态行渲染"""
        renderer.render_status_line("状态", "值", "✅")
        captured = capsys.readouterr()
        assert "状态" in captured.out
        assert "值" in captured.out
        assert "✅" in captured.out

    def test_render_status_line_no_status(self, renderer, capsys):
        """测试无状态的状态行渲染"""
        renderer.render_status_line("状态", "值")
        captured = capsys.readouterr()
        assert "状态" in captured.out
        assert "值" in captured.out
        assert "✅" not in captured.out

    def test_render_result_success(self, renderer, capsys):
        """测试成功结果渲染"""
        renderer.render_result(True, "操作成功")
        captured = capsys.readouterr()
        assert "✅" in captured.out
        assert "操作成功" in captured.out

    def test_render_result_failure(self, renderer, capsys):
        """测试失败结果渲染"""
        renderer.render_result(False, "操作失败")
        captured = capsys.readouterr()
        assert "❌" in captured.out
        assert "操作失败" in captured.out

    def test_render_result_with_details(self, renderer, capsys):
        """测试带详情的成功结果渲染"""
        renderer.render_result(True, "操作成功", ["详情1", "详情2"])
        captured = capsys.readouterr()
        assert "✅" in captured.out
        assert "操作成功" in captured.out
        assert "详情1" in captured.out
        assert "详情2" in captured.out

    def test_render_warning(self, renderer, capsys):
        """测试警告渲染"""
        renderer.render_warning("警告信息")
        captured = capsys.readouterr()
        assert "⚠️" in captured.out
        assert "警告信息" in captured.out

    def test_render_info(self, renderer, capsys):
        """测试信息渲染"""
        renderer.render_info("信息内容")
        captured = capsys.readouterr()
        assert "📝" in captured.out
        assert "信息内容" in captured.out

    def test_render_danger_prompt(self, renderer, capsys):
        """测试危险操作提示渲染"""
        renderer.render_danger_prompt("删除数据", "DELETE")
        captured = capsys.readouterr()
        assert "⚠️ 危险操作" in captured.out
        assert "删除数据" in captured.out
        assert "不可撤销" in captured.out


class TestMenuRendererEdgeCases:
    """测试 MenuRenderer 的边界情况"""

    @pytest.fixture
    def renderer(self):
        return MenuRenderer(UIHelper())

    def test_empty_options(self, renderer, capsys):
        """测试空选项列表"""
        renderer.render_menu(title="空菜单", options=[])
        captured = capsys.readouterr()
        assert "空菜单" in captured.out

    def test_empty_hints(self, renderer, capsys):
        """测试空提示列表"""
        renderer.render_menu(
            title="菜单", options=[("1", "选项", "")], hints=[]
        )
        captured = capsys.readouterr()
        assert "💡" not in captured.out

    def test_none_hints(self, renderer, capsys):
        """测试 None 提示"""
        renderer.render_menu(
            title="菜单", options=[("1", "选项", "")], hints=None
        )
        captured = capsys.readouterr()
        assert "💡" not in captured.out

    def test_none_status_lines(self, renderer, capsys):
        """测试 None 状态行"""
        renderer.render_menu(
            title="菜单", options=[("1", "选项", "")], status_lines=None
        )
        captured = capsys.readouterr()
        # 应该正常渲染，没有状态行
        assert "菜单" in captured.out
