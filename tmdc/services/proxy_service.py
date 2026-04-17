# -*- coding: utf-8 -*-
"""
代理服务模块

提供代理连接管理功能。

注意：UI 交互逻辑已迁移至 menus/proxy_menu.py

主要功能：
- 检查代理连通性
- 保存代理配置
- 获取代理状态
"""

from __future__ import annotations

import socket
import time
from datetime import datetime
from types import ModuleType
from typing import TYPE_CHECKING, Optional, Tuple, Union

if TYPE_CHECKING:
    pass

from ..constants import Constants
from ..tmd_types import IConfig, ILogger, IProxyService, ProxyStatus

_requests: Optional[ModuleType] = None


def _get_requests() -> Optional[ModuleType]:
    """延迟导入 requests"""
    global _requests
    if _requests is None:
        try:
            import requests

            _requests = requests
        except ImportError:
            pass
    return _requests


class ProxyService(IProxyService):
    """代理服务。

    提供代理连接管理、测试和配置功能。

    Attributes:
        config: 配置实例
        logger: 日志实例

    Example:
        >>> from tmdc.services.proxy_service import ProxyService
        >>> service = ProxyService(config, logger)
        >>> is_reachable = service.check_proxy_reachable()
        >>> success, error = service.save_proxy_config(use_proxy=True)
    """

    PROXY_CACHE_TTL = Constants.PROXY_CACHE_TTL

    def __init__(self, config: IConfig, logger: ILogger) -> None:
        """初始化代理服务。

        Args:
            config: 配置实例
            logger: 日志实例
        """
        self.config = config
        self.logger = logger
        self._proxy_reachable_cache: Optional[bool] = None
        self._proxy_check_time: float = 0.0

    def check_proxy_reachable(
        self,
        timeout: Optional[float] = None,
        use_cache: bool = True,
    ) -> bool:
        """检查代理是否可达。

        Args:
            timeout: 超时时间（秒），默认使用 Constants.PROXY_TIMEOUT
            use_cache: 是否使用缓存

        Returns:
            代理是否可达
        """
        effective_timeout = timeout if timeout is not None else Constants.PROXY_TIMEOUT

        if use_cache and self._proxy_reachable_cache is not None:
            elapsed = time.time() - self._proxy_check_time
            if elapsed < self.PROXY_CACHE_TTL:
                return self._proxy_reachable_cache

        if not self.config.use_proxy or not self.config.proxy_hostname:
            return False

        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(effective_timeout)
            result = sock.connect_ex((self.config.proxy_hostname, self.config.proxy_tcp_port))
            is_reachable = result == 0

            self._proxy_reachable_cache = is_reachable
            self._proxy_check_time = time.time()

            return is_reachable
        except Exception:
            return False
        finally:
            if sock:
                sock.close()

    def save_proxy_config(
        self,
        hostname: Optional[str] = None,
        port: Optional[int] = None,
        use_proxy: Optional[bool] = None,
    ) -> Tuple[bool, str]:
        """保存代理配置到 conf.yaml。

        Args:
            hostname: 代理主机名（None 保持原值）
            port: 代理端口（None 保持原值）
            use_proxy: 是否使用代理（None 保持原值）

        Returns:
            (成功标志, 错误消息)
        """
        host = hostname if hostname is not None else self.config.proxy_hostname
        p = port if port is not None else self.config.proxy_tcp_port
        use = use_proxy if use_proxy is not None else self.config.use_proxy

        return self.config.save_proxy(host, p, use)

    def get_status(self) -> ProxyStatus:
        """获取代理状态。

        Returns:
            代理状态信息
        """
        is_reachable = self.check_proxy_reachable(use_cache=True)

        return ProxyStatus(
            is_enabled=self.config.use_proxy,
            is_reachable=is_reachable,
            hostname=self.config.proxy_hostname,
            port=self.config.proxy_tcp_port,
            last_check_time=(
                datetime.fromtimestamp(self._proxy_check_time)
                if self._proxy_check_time > 0
                else None
            ),
        )


__all__ = ["ProxyService"]
