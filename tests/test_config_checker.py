# -*- coding: utf-8 -*-
"""
配置检查器单元测试

测试 ConfigChecker 的各种配置验证场景。
"""

from __future__ import annotations

# 标准库
import unittest
from unittest.mock import MagicMock

# 本地模块
from tmdc.ui.config_checker import ConfigChecker


class TestConfigChecker(unittest.TestCase):
    """ConfigChecker 测试类"""

    def setUp(self):
        """测试前设置"""
        self.config = MagicMock()
        self.logger = MagicMock()
        self.ui = MagicMock()
        self.checker = ConfigChecker(self.config, self.logger, self.ui)

    def test_check_basic_config_all_valid(self):
        """测试所有配置有效的情况"""
        self.config.root_path = "/path"
        self.config.auth_token = "token"
        self.config.ct0 = "ct0"

        result = self.checker.check_basic_config()

        self.assertTrue(result)
        self.ui.pause.assert_not_called()
        self.logger.warning.assert_not_called()

    def test_check_basic_config_missing_root_path(self):
        """测试缺少 root_path 的情况"""
        self.config.root_path = None

        result = self.checker.check_basic_config()

        self.assertFalse(result)
        self.ui.pause.assert_called_once()
        self.logger.warning.assert_called_once_with("核心配置字段缺失")

    def test_check_basic_config_missing_auth_token(self):
        """测试缺少 auth_token 的情况"""
        self.config.root_path = "/path"
        self.config.auth_token = None
        self.config.ct0 = "ct0"

        result = self.checker.check_basic_config()

        self.assertFalse(result)
        self.ui.pause.assert_called_once()
        self.logger.warning.assert_called_once_with("核心配置字段缺失")

    def test_check_basic_config_missing_ct0(self):
        """测试缺少 ct0 的情况"""
        self.config.root_path = "/path"
        self.config.auth_token = "token"
        self.config.ct0 = None

        result = self.checker.check_basic_config()

        self.assertFalse(result)
        self.ui.pause.assert_called_once()
        self.logger.warning.assert_called_once_with("核心配置字段缺失")

    def test_check_basic_config_show_pause_false(self):
        """测试 show_pause=False 时不暂停"""
        self.config.root_path = None

        result = self.checker.check_basic_config(show_pause=False)

        self.assertFalse(result)
        self.ui.pause.assert_not_called()


if __name__ == "__main__":
    unittest.main()
