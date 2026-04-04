# -*- coding: utf-8 -*-
"""代理配置验证模块"""

from __future__ import annotations

from typing import Any, Tuple


def check_proxy_values(host: str, port: Any, use_proxy: bool) -> Tuple[bool, str]:
    """验证代理配置值（纯验证函数，无副作用）

    Args:
        host: 代理主机地址
        port: 代理端口
        use_proxy: 是否使用代理

    Returns:
        Tuple[bool, str]: (是否有效, 错误信息)

    Examples:
        >>> check_proxy_values("127.0.0.1", 7890, True)
        (True, '')
        >>> check_proxy_values("", 7890, True)
        (False, '代理主机地址无效（不能为空）')
        >>> check_proxy_values("127.0.0.1", 99999, True)
        (False, '代理端口 99999 超出范围(1-65535)')
        >>> check_proxy_values("127.0.0.1", 7890, False)
        (True, '')
    """
    if not use_proxy:
        return True, ""

    if not host or not isinstance(host, str) or not host.strip():
        return False, "代理主机地址无效（不能为空）"

    host = host.strip()
    if " " in host or "\n" in host or "\t" in host:
        return False, "代理主机地址包含非法字符"

    try:
        p = int(port)
        if not (1 <= p <= 65535):
            return False, f"代理端口 {p} 超出范围(1-65535)"
    except (ValueError, TypeError):
        return False, f"代理端口格式无效: {port}"

    return True, ""


__all__ = ["check_proxy_values"]
