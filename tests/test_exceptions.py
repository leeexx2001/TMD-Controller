# -*- coding: utf-8 -*-
"""测试 exceptions.py"""

import pytest
from tmdc.exceptions import (
    TMDError,
    ConfigError,
    DownloadError,
    DatabaseError,
    ValidationError,
    AuthenticationError,
    ProxyError,
    ServiceError,
)


class TestExceptions:
    """异常类测试"""

    def test_base_exception(self):
        """测试基础异常"""
        assert issubclass(TMDError, Exception)

    def test_config_error_inherits(self):
        """测试配置异常继承"""
        assert issubclass(ConfigError, TMDError)
        with pytest.raises(TMDError):
            raise ConfigError("config error")

    def test_download_error_inherits(self):
        """测试下载异常继承"""
        assert issubclass(DownloadError, TMDError)
        with pytest.raises(TMDError):
            raise DownloadError("download error")

    def test_database_error_inherits(self):
        """测试数据库异常继承"""
        assert issubclass(DatabaseError, TMDError)
        with pytest.raises(TMDError):
            raise DatabaseError("database error")

    def test_validation_error_inherits(self):
        """测试验证异常继承"""
        assert issubclass(ValidationError, TMDError)
        with pytest.raises(TMDError):
            raise ValidationError("validation error")

    def test_proxy_error_inherits(self):
        """测试代理异常继承"""
        assert issubclass(ProxyError, TMDError)
        with pytest.raises(TMDError):
            raise ProxyError("proxy error")

    def test_authentication_error_inherits(self):
        """测试认证异常继承"""
        assert issubclass(AuthenticationError, TMDError)
        with pytest.raises(TMDError):
            raise AuthenticationError("auth error")

    def test_service_error_inherits(self):
        """测试服务异常继承"""
        assert issubclass(ServiceError, TMDError)
        with pytest.raises(TMDError):
            raise ServiceError("service error")

    def test_exception_message(self):
        """测试异常消息"""
        try:
            raise ConfigError("test message")
        except ConfigError as e:
            assert str(e) == "test message"

    def test_exception_with_details(self):
        """测试带详情的异常"""
        try:
            raise ConfigError("test message", details={"key": "value"})
        except ConfigError as e:
            assert "test message" in str(e)
            assert e.details == {"key": "value"}
