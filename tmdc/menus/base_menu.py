# -*- coding: utf-8 -*-
"""
菜单基类模块

定义菜单的通用接口和基础实现。
"""

from __future__ import annotations

# 标准库
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Callable, List, Optional, Tuple

if TYPE_CHECKING:
    from tmdc.tmd_types import IConfig, ILogger, IUIHelper

# 第三方库（无）

# 本地模块
from ..ui.config_checker import ConfigChecker


class BaseMenu(ABC):
    """
    菜单基类

    定义菜单的通用接口和基础实现。

    Attributes:
        ui: UI 辅助实例
        logger: 日志实例
        config: 配置实例
        _renderer: 菜单渲染器实例
    """

    def __init__(
        self,
        ui: "IUIHelper",
        logger: "ILogger",
        config: "IConfig",
    ) -> None:
        """
        初始化菜单基类

        Args:
            ui: UI 辅助实例
            logger: 日志实例
            config: 配置实例
        """
        self.ui = ui
        self.logger = logger
        self.config = config
        # 初始化配置检查器
        self._config_checker = ConfigChecker(config, logger, ui)
        # 初始化菜单渲染器（局部导入避免循环）
        from ..ui.menu_renderer import MenuRenderer

        self._renderer = MenuRenderer(ui)

    @abstractmethod
    def show(self) -> None:
        """
        显示菜单

        子类必须实现此方法来显示菜单界面。
        """
        ...

    def _check_config_or_return(
        self, show_pause: bool = True, check_config_exists: bool = False
    ) -> bool:
        """
        检查配置是否完整有效

        检查配置是否存在以及核心配置字段是否完整。

        Args:
            show_pause: 配置无效时是否暂停等待用户确认
            check_config_exists: 是否检查配置文件存在性

        Returns:
            配置有效返回 True，否则返回 False
        """
        return self._config_checker.check_basic_config(
            show_pause=show_pause, check_config_exists=check_config_exists
        )

    # ==================== 新增：标准模板方法 ====================

    def _run_menu_loop(
        self,
        title: str,
        options: List[Tuple[str, str, str]],
        handlers: dict,
        status_lines: Optional[List[Tuple[str, str, str]]] = None,
        hints: Optional[List[str]] = None,
        exit_key: str = "0",
    ) -> None:
        """标准菜单循环模板

        Args:
            title: 菜单标题
            options: 选项列表 [(key, label, desc), ...]
            handlers: 处理器字典 {key: callable}
            status_lines: 状态行
            hints: 提示信息
            exit_key: 退出键
        """
        while True:
            self._renderer.render_menu(title, options, status_lines, hints)
            choice = self._get_menu_choice()

            if choice == exit_key:
                break

            handler = handlers.get(choice)
            if handler:
                handler()
            # 无效选择直接继续循环，不报错

    def _get_menu_choice(self, prompt: str = "请选择") -> str:
        """获取菜单选择（统一输入处理）

        Returns:
            标准化后的用户输入（大写、去空白）
        """
        result = self.ui.safe_input(f"\n{prompt}: ", allow_empty=True)
        return result.strip().upper() if result else ""

    def _show_result(
        self, success: bool, message: str, details: Optional[List[str]] = None
    ) -> None:
        """显示操作结果"""
        self._renderer.render_result(success, message, details)

    def _confirm_dangerous(self, action_desc: str, confirm_text: str) -> bool:
        """危险操作确认

        Args:
            action_desc: 操作描述
            confirm_text: 需要输入的确认文本

        Returns:
            确认通过返回 True
        """
        self._renderer.render_danger_prompt(action_desc, confirm_text)
        user_input = self.ui.safe_input(
            f"请输入 '{confirm_text}' 确认: ", allow_empty=True
        )
        return user_input is not None and user_input.upper() == confirm_text.upper()

    def _get_choice_index(
        self, max_index: int, prompt: str = "选择序号"
    ) -> Optional[int]:
        """获取有效的序号选择

        Args:
            max_index: 最大有效序号（1-based）
            prompt: 提示文本

        Returns:
            0-based 索引，无效返回 None
        """
        choice = self.ui.safe_input(f"\n{prompt} (回车取消): ", allow_empty=True)
        if not choice or not choice.isdigit():
            return None
        idx = int(choice) - 1
        if not (0 <= idx < max_index):
            print("❌ 无效序号")
            self.ui.pause()
            return None
        return idx


__all__ = ["BaseMenu"]
