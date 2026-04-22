# -*- coding: utf-8 -*-
"""
菜单渲染组件

提供统一的菜单界面渲染功能，包括：
- 菜单框架渲染（标题、选项、分隔线）
- 状态行渲染
- 提示信息渲染
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Tuple

if TYPE_CHECKING:
    from ..tmd_types import IUIHelper

from ..utils.text_utils import display_width


class MenuRenderer:
    """菜单渲染器

    统一渲染菜单界面元素。
    """

    def __init__(self, ui: "IUIHelper") -> None:
        self.ui = ui

    def render_menu(
        self,
        title: str,
        options: List[Tuple[str, str, str]],
        status_lines: Optional[List[Tuple[str, str, str]]] = None,
        hints: Optional[List[str]] = None,
    ) -> None:
        """渲染完整菜单

        Args:
            title: 菜单标题
            options: 选项列表 [(key, label, desc), ...]
            status_lines: 状态行列表 [(label, value, status_icon), ...]
            hints: 提示信息列表
        """
        self.ui.clear_screen()
        self.ui.show_header(title)

        if status_lines:
            for label, value, status in status_lines:
                self.render_status_line(label, value, status)
            print()
            self.ui.print_separator()

        for key, label, desc in options:
            label_width = display_width(label)
            padding = 12 - label_width + len(label)  # 调整填充以补偿中文字符
            # 如果描述为空，不显示箭头
            if desc:
                print(f"  [{key}] {label:<{padding}} → {desc}")
            else:
                print(f"  [{key}] {label}")

        self.ui.print_separator()

        if hints:
            for hint in hints:
                print(f"💡 {hint}")

    def render_status_line(
        self, label: str, value: str, status: str = ""
    ) -> None:
        """渲染状态行

        Args:
            label: 标签名
            value: 值
            status: 状态图标/文本
        """
        status_str = f" [{status}]" if status else ""
        print(f"  {label:<10} {value}{status_str}")

    def render_result(self, success: bool, message: str, details: Optional[List[str]] = None) -> None:
        """渲染操作结果

        Args:
            success: 是否成功
            message: 主消息
            details: 详情列表
        """
        icon = "✅" if success else "❌"
        print(f"\n{icon} {message}")
        if details:
            for detail in details:
                print(f"   {detail}")

    def render_warning(self, message: str, details: Optional[List[str]] = None) -> None:
        """渲染警告信息"""
        print(f"\n⚠️ {message}")
        if details:
            for detail in details:
                print(f"   {detail}")

    def render_info(self, message: str) -> None:
        """渲染信息提示"""
        print(f"\n📝 {message}")

    def render_danger_prompt(self, action_desc: str, confirm_text: str) -> None:
        """渲染危险操作提示"""
        print(f"\n⚠️ 危险操作: {action_desc}")
        print("此操作不可撤销！")


__all__ = ["MenuRenderer"]
