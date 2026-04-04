# -*- coding: utf-8 -*-
"""Cookie 服务测试"""

import pytest
from unittest.mock import Mock
from pathlib import Path

from tmdc.services.cookie_service import CookieService
from tmdc.tmd_types import OperationResult


class TestToggleCookiesDisabled:
    """测试 toggle_cookies_disabled 方法"""

    @pytest.fixture
    def mock_services(self, tmp_path):
        config = Mock()
        config.cookie_file = tmp_path / "additional_cookies.yaml"
        logger = Mock()
        return config, logger

    def test_returns_operation_result_type(self, mock_services):
        """返回值类型必须是 OperationResult"""
        config, logger = mock_services

        service = CookieService(config=config, logger=logger)
        result = service.toggle_cookies_disabled()

        assert isinstance(result, OperationResult)

    def test_no_print_output(self, mock_services, capsys):
        """不产生 print 输出"""
        config, logger = mock_services

        service = CookieService(config=config, logger=logger)
        service.toggle_cookies_disabled()

        captured = capsys.readouterr()
        assert captured.out == ""


class TestParseCookieString:
    """测试 parse_cookie_string 函数（已迁移到 validators.py）"""

    def test_extracts_auth_token_and_ct0(self):
        """正确提取 auth_token 和 ct0"""
        from tmdc.utils.validators.cookie import parse_cookie_string

        cookie_str = "auth_token=abc123def456789012abcdef; ct0=789abc456def012abcdef345; other=value123456"

        result = parse_cookie_string(cookie_str)

        assert result is not None
        assert result["auth_token"] == "abc123def456789012abcdef"
        assert result["ct0"] == "789abc456def012abcdef345"

    def test_returns_none_when_missing_auth_token(self):
        """缺少 auth_token 时返回 None"""
        from tmdc.utils.validators.cookie import parse_cookie_string

        cookie_str = "ct0=xyz789; other=value"

        result = parse_cookie_string(cookie_str)

        assert result is None
