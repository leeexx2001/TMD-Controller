# -*- coding: utf-8 -*-
"""集成测试 - 配置管理流程"""

import os
import tempfile
from pathlib import Path
import pytest

from tmdc.config.config import TMDConfig
from tmdc.container import Container


class TestConfigIntegration:
    """配置管理集成测试"""

    def setup_method(self):
        """每个测试前重置"""
        Container.reset()

    def test_config_default_values(self):
        """测试配置默认值"""
        config = TMDConfig()
        assert config.max_download_routine > 0
        assert config.file_batch_size >= 1

    def test_config_path_setup(self):
        """测试配置路径设置"""
        config = TMDConfig()
        assert config.config_dir is not None
        assert config.config_file is not None

    def test_container_config_integration(self):
        """测试容器配置集成"""
        container = Container.get_instance()
        config = TMDConfig()
        container.register("config", config)

        resolved = container.resolve("config")
        assert resolved is config

    def test_config_validation(self):
        """测试配置验证"""
        config = TMDConfig()
        assert hasattr(config, "auth_token")
        assert hasattr(config, "ct0")
        assert hasattr(config, "root_path")


class TestInputParserIntegration:
    """输入解析器集成测试"""

    def test_parse_url_integration(self):
        """测试 URL 解析集成"""
        from tmdc.parsers.input_parser import InputParser

        test_cases = [
            ("https://twitter.com/username", "user"),
            ("https://x.com/i/lists/123456789012", "list"),
            ("@username", "user"),
        ]

        for input_str, expected_type in test_cases:
            result_type, value, _ = InputParser.parse(input_str)
            assert result_type == expected_type, f"Failed for {input_str}"

    def test_batch_parse_integration(self):
        """测试批量解析集成"""
        from tmdc.parsers.input_parser import InputParser

        batch_input = "user1, user2, @user3, https://twitter.com/user4"
        items = InputParser.parse_batch(batch_input)

        assert len(items) >= 3
        assert all(item[0] == "user" for item in items)


class TestServiceIntegration:
    """服务集成测试"""

    def setup_method(self):
        """每个测试前重置"""
        Container.reset()

    def test_container_service_registration(self):
        """测试容器服务注册"""
        container = Container.get_instance()

        from tmdc.config.config import TMDConfig
        from tmdc.ui.ui_helper import UIHelper

        config = TMDConfig()
        ui = UIHelper()

        container.register("config", config)
        container.register("ui", ui)

        assert container.has("config")
        assert container.has("ui")

    def test_service_factory_pattern(self):
        """测试服务工厂模式"""
        container = Container.get_instance()

        call_count = [0]

        def create_service():
            call_count[0] += 1
            return {"id": call_count[0]}

        container.register_factory("test_service", create_service)

        s1 = container.resolve("test_service")
        s2 = container.resolve("test_service")

        assert s1["id"] == 1
        assert s2["id"] == 1
        assert call_count[0] == 1
