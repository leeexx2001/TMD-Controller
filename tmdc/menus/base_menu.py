# -*- coding: utf-8 -*-
"""
菜单基类模块

定义菜单的通用接口和基础实现。
"""

from __future__ import annotations

# 标准库
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

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


__all__ = ["BaseMenu"]
