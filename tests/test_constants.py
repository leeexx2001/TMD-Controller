# -*- coding: utf-8 -*-
"""测试 constants.py"""

import pytest
from tmdc.constants import VERSION, Constants, C


class TestConstants:
    """常量模块测试"""

    def test_version_format(self):
        """测试版本号格式"""
        assert isinstance(VERSION, str)
        parts = VERSION.split(".")
        assert len(parts) >= 2
        assert all(part.isdigit() for part in parts)

    def test_constants_class_exists(self):
        """测试常量类存在"""
        assert hasattr(Constants, "USERNAME_MAX_LEN")
        assert hasattr(Constants, "LIST_ID_MIN_LEN")
        assert hasattr(Constants, "COOKIE_MIN_LEN")
        assert hasattr(Constants, "MAX_DOWNLOAD_ROUTINE")

    def test_constants_values(self):
        """测试常量值正确"""
        assert Constants.USERNAME_MAX_LEN == 15
        assert Constants.LIST_ID_MIN_LEN == 10
        assert Constants.COOKIE_MIN_LEN == 50
        assert Constants.MAX_DOWNLOAD_ROUTINE == 100

    def test_constants_alias(self):
        """测试常量别名"""
        assert C is Constants
        assert C.USERNAME_MAX_LEN == Constants.USERNAME_MAX_LEN

    def test_ui_constants(self):
        """测试 UI 常量"""
        assert Constants.UI_WIDTH == 62
        assert Constants.BATCH_MAX_DISPLAY == 5
        assert Constants.LOG_PAGE_SIZE == 20

    def test_proxy_constants(self):
        """测试代理常量"""
        assert Constants.PROXY_TIMEOUT == 5.0
        assert Constants.PROXY_CACHE_TTL == 5.0

    def test_remedy_constants(self):
        """测试补救下载常量"""
        assert Constants.REMEDY_TIMEOUT == 30
        assert Constants.REMEDY_MAX_SIZE_MB == 800
        assert Constants.REMEDY_RETRY == 2
