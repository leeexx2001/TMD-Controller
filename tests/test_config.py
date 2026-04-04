# -*- coding: utf-8 -*-
"""测试 config.py"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from tmdc.config.config import TMDConfig


class TestTMDConfigInit:
    """TMDConfig 初始化测试"""

    def test_default_init(self):
        """测试默认初始化"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "conf.yaml"
            config = TMDConfig(custom_config_path=str(config_path))
            assert config.proxy_hostname == "127.0.0.1"
            assert config.proxy_tcp_port == 7897
            assert config.use_proxy is True
            assert config.file_batch_size == 3

    def test_custom_config_path(self):
        """测试自定义配置路径"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "custom" / "conf.yaml"
            config = TMDConfig(custom_config_path=str(config_path))
            assert config.config_file == config_path

    def test_config_paths_setup(self):
        """测试配置路径设置"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "conf.yaml"
            config = TMDConfig(custom_config_path=str(config_path))
            assert config.config_dir == config_path.parent
            assert config.cookie_file.name == "additional_cookies.yaml"
            assert config.log_file.name == "tmd_controller.log"


class TestTMDConfigProperties:
    """TMDConfig 属性测试"""

    def test_default_quick_list_id_empty(self):
        """测试空快速列表"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "conf.yaml"
            config = TMDConfig(custom_config_path=str(config_path))
            assert config.default_quick_list_id is None

    def test_default_quick_list_id_with_ids(self):
        """测试有快速列表"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "conf.yaml"
            config = TMDConfig(custom_config_path=str(config_path))
            config.quick_list_ids = ["1234567890", "0987654321"]
            assert config.default_quick_list_id == "1234567890"

    def test_is_batch_delay_success_enabled_false(self):
        """测试成功延迟未启用"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "conf.yaml"
            config = TMDConfig(custom_config_path=str(config_path))
            assert config.is_batch_delay_success_enabled is False

    def test_is_batch_delay_success_enabled_true(self):
        """测试成功延迟已启用"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "conf.yaml"
            config = TMDConfig(custom_config_path=str(config_path))
            config.batch_delay_success_max = 10
            assert config.is_batch_delay_success_enabled is True

    def test_is_batch_delay_fail_enabled_false(self):
        """测试失败延迟未启用"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "conf.yaml"
            config = TMDConfig(custom_config_path=str(config_path))
            assert config.is_batch_delay_fail_enabled is False

    def test_is_batch_delay_fail_enabled_true(self):
        """测试失败延迟已启用"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "conf.yaml"
            config = TMDConfig(custom_config_path=str(config_path))
            config.batch_delay_fail_max = 10
            assert config.is_batch_delay_fail_enabled is True

    def test_db_path_with_root(self):
        """测试有根路径时的数据库路径"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "conf.yaml"
            config = TMDConfig(custom_config_path=str(config_path))
            config.root_path = "/path/to/downloads"
            assert config.db_path == Path("/path/to/downloads/.data/foo.db")

    def test_db_path_without_root(self):
        """测试无根路径时的数据库路径"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "conf.yaml"
            config = TMDConfig(custom_config_path=str(config_path))
            config.root_path = None
            assert config.db_path is None


class TestTMDConfigLoadFromConfig:
    """从配置加载测试"""

    def test_load_proxy_from_config_valid(self):
        """测试加载有效代理配置"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "conf.yaml"
            config = TMDConfig(custom_config_path=str(config_path))
            config._load_proxy_from_config({
                "proxy_hostname": "192.168.1.1",
                "proxy_tcp_port": 8080,
                "use_proxy": True,
            })
            assert config.proxy_hostname == "192.168.1.1"
            assert config.proxy_tcp_port == 8080

    def test_load_quick_lists_from_config_valid(self):
        """测试加载有效快速列表"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "conf.yaml"
            config = TMDConfig(custom_config_path=str(config_path))
            config._load_quick_lists_from_config({
                "quick_list_ids": ["1234567890", "0987654321"]
            })
            assert len(config.quick_list_ids) == 2

    def test_load_quick_lists_from_config_invalid(self):
        """测试加载无效快速列表"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "conf.yaml"
            config = TMDConfig(custom_config_path=str(config_path))
            config._load_quick_lists_from_config({
                "quick_list_ids": ["short", "invalid"]
            })
            assert len(config.quick_list_ids) == 0

    def test_load_batch_config_from_config_valid(self):
        """测试加载有效分批配置"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "conf.yaml"
            config = TMDConfig(custom_config_path=str(config_path))
            config._load_batch_config_from_config({"file_batch_size": 10})
            assert config.file_batch_size == 10

    def test_load_batch_config_from_config_invalid(self):
        """测试加载无效分批配置"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "conf.yaml"
            config = TMDConfig(custom_config_path=str(config_path))
            original_size = config.file_batch_size
            config._load_batch_config_from_config({"file_batch_size": 100})
            assert config.file_batch_size == original_size

    def test_load_batch_delay_config(self):
        """测试加载延迟配置"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "conf.yaml"
            config = TMDConfig(custom_config_path=str(config_path))
            config._load_batch_delay_config({
                "batch_delay": {
                    "success": {"min": 5, "max": 10},
                    "fail": {"min": 10, "max": 20},
                }
            })
            assert config.batch_delay_success_min == 5
            assert config.batch_delay_success_max == 10
            assert config.batch_delay_fail_min == 10
            assert config.batch_delay_fail_max == 20

    def test_load_core_config_from_config(self):
        """测试加载核心配置"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "conf.yaml"
            config = TMDConfig(custom_config_path=str(config_path))
            config._load_core_config_from_config({
                "root_path": "/path/to/downloads",
                "cookie": {
                    "auth_token": "a" * 40,
                    "ct0": "b" * 64,
                },
                "max_download_routine": 5,
            })
            assert config.root_path == "/path/to/downloads"
            assert config.auth_token == "a" * 40
            assert config.ct0 == "b" * 64
            assert config.max_download_routine == 5

    def test_load_quick_list_interval(self):
        """测试加载列表间间隔"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "conf.yaml"
            config = TMDConfig(custom_config_path=str(config_path))
            config._load_quick_list_interval({"quick_list_interval": 30})
            assert config.quick_list_interval == 30


class TestTMDConfigReadConfig:
    """配置读取测试"""

    def test_read_config_nonexistent_file(self):
        """测试读取不存在的配置文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "conf.yaml"
            config = TMDConfig(custom_config_path=str(config_path))
            result = config._read_config()
            assert result == {}

    def test_read_config_valid_yaml(self):
        """测试读取有效的 YAML 文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "conf.yaml"
            config_path.write_text("proxy_hostname: 192.168.1.1\nproxy_tcp_port: 8080\n")
            config = TMDConfig(custom_config_path=str(config_path))
            result = config._read_config()
            assert result["proxy_hostname"] == "192.168.1.1"
            assert result["proxy_tcp_port"] == 8080

    def test_read_config_empty_yaml(self):
        """测试读取空的 YAML 文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "conf.yaml"
            config_path.write_text("")
            config = TMDConfig(custom_config_path=str(config_path))
            result = config._read_config()
            assert result == {}


class TestTMDConfigSaveQuickListIds:
    """保存快速列表测试"""

    def test_save_quick_list_ids_new_ids(self):
        """测试保存新的快速列表"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "conf.yaml"
            config = TMDConfig(custom_config_path=str(config_path))
            success, error = config.save_quick_list_ids(["1234567890"])
            assert success is True
            assert error == ""
            assert "1234567890" in config.quick_list_ids

    def test_save_quick_list_ids_none(self):
        """测试保存空快速列表"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "conf.yaml"
            config = TMDConfig(custom_config_path=str(config_path))
            config.quick_list_ids = ["1234567890"]
            success, error = config.save_quick_list_ids(None)
            assert success is True


class TestTMDConfigSaveConfigField:
    """保存配置字段测试"""

    def test_save_config_field_simple(self):
        """测试保存简单字段"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "conf.yaml"
            config = TMDConfig(custom_config_path=str(config_path))
            success, error = config._save_config_field("test_field", "test_value")
            assert success is True
            assert error == ""

    def test_save_config_field_nested(self):
        """测试保存嵌套字段"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "conf.yaml"
            config = TMDConfig(custom_config_path=str(config_path))
            success, error = config._save_config_field(
                "nested.field", "test_value"
            )
            assert success is True


class TestTMDConfigSaveProxy:
    """保存代理配置测试"""

    def test_save_proxy_valid(self):
        """测试保存有效代理配置"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "conf.yaml"
            config = TMDConfig(custom_config_path=str(config_path))
            success, error = config.save_proxy("192.168.1.1", 8080, True)
            assert success is True
            assert error == ""
            assert config.proxy_hostname == "192.168.1.1"
            assert config.proxy_tcp_port == 8080

    def test_save_proxy_invalid_port(self):
        """测试保存无效端口"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "conf.yaml"
            config = TMDConfig(custom_config_path=str(config_path))
            success, error = config.save_proxy("192.168.1.1", 70000, True)
            assert success is False
            assert "端口" in error

    def test_save_proxy_rollback_on_failure(self):
        """测试写入失败时回滚"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "conf.yaml"
            config = TMDConfig(custom_config_path=str(config_path))

            config.proxy_hostname = "127.0.0.1"
            config.proxy_tcp_port = 7897
            config.use_proxy = True

            with patch.object(config, '_read_config', side_effect=Exception("模拟失败")):
                success, error = config.save_proxy("192.168.1.1", 8080, True)
                assert success is False
                assert config.proxy_hostname == "127.0.0.1"
                assert config.proxy_tcp_port == 7897


class TestTMDConfigSaveBatchConfig:
    """保存批量配置测试"""

    def test_save_batch_config_valid(self):
        """测试保存有效批量配置"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "conf.yaml"
            config = TMDConfig(custom_config_path=str(config_path))
            success, error = config.save_batch_config(10)
            assert success is True
            assert error == ""
            assert config.file_batch_size == 10

    def test_save_batch_config_invalid(self):
        """测试保存无效批量配置"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "conf.yaml"
            config = TMDConfig(custom_config_path=str(config_path))
            success, error = config.save_batch_config(100)
            assert success is False
            assert "1-50" in error

    def test_save_batch_config_rollback_on_failure(self):
        """测试写入失败时回滚"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "conf.yaml"
            config = TMDConfig(custom_config_path=str(config_path))

            config.file_batch_size = 3

            with patch.object(config, '_read_config', side_effect=Exception("模拟失败")):
                success, error = config.save_batch_config(10)
                assert success is False
                assert config.file_batch_size == 3
