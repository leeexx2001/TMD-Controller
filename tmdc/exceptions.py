# -*- coding: utf-8 -*-
"""
TMD 异常类定义模块

定义统一的异常类层次结构，便于错误处理和分类。
"""

# 标准库
from typing import Dict, Optional

# 第三方库（无）

# 本地模块（无）


class TMDError(Exception):
    """
    TMD 基础异常类

    所有 TMD 相关异常的基类，提供统一的异常处理接口。

    Attributes:
        message: 错误消息
        details: 额外的错误详情

    Example:
        >>> raise TMDError("操作失败", details={"code": 500})
        TMDError: 操作失败
    """

    def __init__(self, message: str, *, details: Optional[Dict[str, str]] = None) -> None:
        """
        初始化异常

        Args:
            message: 错误消息
            details: 额外的错误详情（可选）
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        """返回异常的字符串表示"""
        if self.details:
            return f"{self.message} (details: {self.details})"
        return self.message


class ConfigError(TMDError):
    """
    配置相关异常

    当配置加载、验证或保存失败时抛出。

    Example:
        >>> raise ConfigError("无效的代理配置", details={"proxy": "127.0.0.1:7897"})
        ConfigError: 无效的代理配置
    """


class DownloadError(TMDError):
    """
    下载相关异常

    当下载操作失败时抛出。

    Example:
        >>> raise DownloadError("下载超时", details={"url": "https://example.com"})
        DownloadError: 下载超时
    """


class DatabaseError(TMDError):
    """
    数据库相关异常

    当数据库操作失败时抛出。

    Example:
        >>> raise DatabaseError("数据库连接失败", details={"db_path": "/path/to/db"})
        DatabaseError: 数据库连接失败
    """


class ValidationError(TMDError):
    """
    验证相关异常

    当数据验证失败时抛出。

    Example:
        >>> raise ValidationError("用户名格式无效", details={"username": "invalid@user"})
        ValidationError: 用户名格式无效
    """


class AuthenticationError(TMDError):
    """
    认证相关异常

    当认证失败时抛出（如 Cookie 无效）。

    Example:
        >>> raise AuthenticationError("Cookie 已过期")
        AuthenticationError: Cookie 已过期
    """


class ProxyError(TMDError):
    """
    代理相关异常

    当代理连接或配置失败时抛出。

    Example:
        >>> raise ProxyError("代理连接超时", details={"proxy": "127.0.0.1:7897"})
        ProxyError: 代理连接超时
    """


class ServiceError(TMDError):
    """
    服务相关异常

    当服务初始化或运行失败时抛出。

    Example:
        >>> raise ServiceError("下载服务初始化失败")
        ServiceError: 下载服务初始化失败
    """


__all__ = [
    "TMDError",
    "ConfigError",
    "DownloadError",
    "DatabaseError",
    "ValidationError",
    "AuthenticationError",
    "ProxyError",
    "ServiceError",
]
