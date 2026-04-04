# -*- coding: utf-8 -*-
"""
配置检查工具模块

提供统一的配置验证功能，避免代码重复。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tmdc.tmd_types import IConfig, ILogger, IUIHelper


class ConfigChecker:
    """
    配置检查器

    提供统一的配置验证功能，支持自定义验证逻辑。

    Attributes:
        config: 配置实例
        logger: 日志实例
        ui: UI 辅助实例

    Example:
        >>> checker = ConfigChecker(config, logger, ui)
        >>> if checker.check_basic_config():
        ...     print("配置有效")
    """

    def __init__(
        self,
        config: "IConfig",
        logger: "ILogger",
        ui: "IUIHelper",
    ) -> None:
        """
        初始化配置检查器

        Args:
            config: 配置实例
            logger: 日志实例
            ui: UI 辅助实例
        """
        self.config = config
        self.logger = logger
        self.ui = ui

    def _handle_invalid_config(
        self, message: str, log_msg: str, show_pause: bool
    ) -> bool:
        """
        处理无效配置的通用方法

        Args:
            message: 显示给用户的消息
            log_msg: 记录到日志的消息
            show_pause: 是否暂停等待用户确认

        Returns:
            始终返回 False
        """
        print(message)
        self.logger.warning(log_msg)
        if show_pause:
            self.ui.pause()
        return False

    def check_basic_config(
        self, show_pause: bool = True, check_config_exists: bool = False
    ) -> bool:
        """
        检查基本配置是否完整

        检查配置文件是否存在以及 root_path、auth_token、ct0 是否已配置。

        Args:
            show_pause: 配置无效时是否暂停等待用户确认
            check_config_exists: 是否检查配置文件存在性

        Returns:
            配置有效返回 True，否则返回 False
        """
        if check_config_exists:
            config_file = getattr(self.config, "config_file", None)
            if config_file and not config_file.exists():
                return self._handle_invalid_config(
                    "❌ 尚未配置！请先运行 [C] 配置向导 → [1] TMD核心配置。",
                    "用户尝试操作但未配置",
                    show_pause,
                )

        if not self.config.auth_token or not self.config.ct0 or not self.config.root_path:
            return self._handle_invalid_config(
                "❌ 核心配置不完整！请运行 [C] 配置向导 → [1] TMD核心配置\n💡 需要配置: auth_token, ct0, root_path",
                "核心配置字段缺失",
                show_pause,
            )

        return True


__all__ = ["ConfigChecker"]
