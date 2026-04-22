# -*- coding: utf-8 -*-
"""
代理管理菜单模块

从 proxy_service.py 迁移 UI 交互逻辑。
提供代理设置管理的菜单界面。

主要功能：
- 开启/关闭代理
- 修改代理地址
- 测试端口连通性
- 深度测试（HTTP 请求）
"""

from __future__ import annotations

import time
from types import ModuleType
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from tmdc.services.proxy_service import ProxyService
    from tmdc.tmd_types import IConfig, ILogger, IUIHelper

from tmdc.utils.validators.proxy import check_proxy_values
from .base_menu import BaseMenu

_requests: Optional[ModuleType] = None

try:
    import requests as _requests_module

    _requests = _requests_module
except ImportError:
    pass


def _get_requests() -> Optional[ModuleType]:
    """延迟导入 requests 模块"""
    return _requests


class ProxyMenu(BaseMenu):
    """代理管理菜单。

    提供代理设置管理的菜单界面。

    Attributes:
        ui: UI 辅助实例
        logger: 日志实例
        config: 配置实例
        proxy_service: 代理服务实例

    Example:
        >>> from tmdc.menus.proxy_menu import ProxyMenu
        >>> menu = ProxyMenu(ui, logger, config, proxy_service)
        >>> menu.show()
    """

    def __init__(
        self,
        ui: "IUIHelper",
        logger: "ILogger",
        config: "IConfig",
        proxy_service: "ProxyService",
    ) -> None:
        """初始化代理管理菜单。

        Args:
            ui: UI 辅助实例
            logger: 日志实例
            config: 配置实例
            proxy_service: 代理服务实例
        """
        super().__init__(ui, logger, config)
        self.proxy_service = proxy_service

    def show(self) -> None:
        """显示代理管理菜单"""
        options = [
            ("1", "开启代理", "启用代理连接"),
            ("2", "关闭代理", "禁用代理连接"),
            ("3", "修改代理地址", "更改主机和端口"),
            ("4", "测试端口", "检查代理端口是否可达"),
            ("5", "深度测试", "通过代理访问 Twitter"),
            ("0", "返回上级菜单", ""),
        ]

        handlers = {
            "1": lambda: self._toggle_proxy(True),
            "2": lambda: self._toggle_proxy(False),
            "3": self._edit_proxy_settings,
            "4": self._test_proxy_port,
            "5": self._test_proxy_http,
        }

        while True:
            self.ui.clear_screen()
            self.ui.show_header("代理管理")

            status = "开启" if self.config.use_proxy else "关闭"
            self.ui.print_status_line("代理状态", status)
            self.ui.print_status_line(
                "代理地址", f"{self.config.proxy_hostname}:{self.config.proxy_tcp_port}"
            )

            self._display_reachability()

            self.ui.print_separator()
            for key, label, desc in options:
                self.ui.print_menu_option(key, label, desc)
            self.ui.print_separator()

            choice = self._get_menu_choice("请选择 [1-5,0]")

            if choice == "0":
                break

            handler = handlers.get(choice)
            if handler:
                handler()
            else:
                continue

    def _display_reachability(self) -> None:
        """显示代理连通性状态"""
        if (
            hasattr(self.proxy_service, "_proxy_reachable_cache")
            and hasattr(self.proxy_service, "_proxy_check_time")
            and time.time() - self.proxy_service._proxy_check_time < 30
        ):
            is_reachable = self.proxy_service._proxy_reachable_cache
        else:
            is_reachable = self.proxy_service.check_proxy_reachable(timeout=1.0)

        if self.config.use_proxy:
            if is_reachable:
                self.ui.print_status_line("连通性", "✅ 端口可达")
            else:
                self.ui.print_status_line("连通性", "❌ 端口不可达")
        else:
            self.ui.print_status_line("连通性", "- (代理未启用)")
        print()

    def _toggle_proxy(self, enable: bool) -> None:
        """切换代理开关状态"""
        if enable == self.config.use_proxy:
            status = "已是开启状态" if enable else "已是关闭状态"
            print(f"\n📝 代理{status}")
            self.ui.pause()
            return

        if enable:
            is_valid, error = check_proxy_values(
                self.config.proxy_hostname,
                self.config.proxy_tcp_port,
                True,
            )
            if not is_valid:
                print(f"\n❌ 当前代理配置无效: {error}")
                print(f"💡 当前值: {self.config.proxy_hostname}:{self.config.proxy_tcp_port}")
                print("💡 先使用 [3] 修改代理地址，修正配置错误")
                self.ui.pause()
                return

        old_use = self.config.use_proxy

        success, error_msg = self.proxy_service.save_proxy_config(use_proxy=enable)

        if success:
            status = "开启" if enable else "关闭"
            print(f"\n✅ 代理已{status}并保存到配置")

            if enable and not self.proxy_service.check_proxy_reachable(timeout=1.0):
                print("\n⚠️ 代理端口当前不可达！")
                print("    请确认代理软件已运行")
                print(f"    当前配置: {self.config.proxy_hostname}:{self.config.proxy_tcp_port}")
        else:
            self.config.use_proxy = old_use
            print(f"\n❌ 保存代理配置失败: {error_msg}")
            print("💡 配置未更改，请检查文件权限")

        self.ui.pause()

    def _edit_proxy_settings(self) -> None:
        """交互式修改代理配置"""
        print(f"\n当前配置: {self.config.proxy_hostname}:{self.config.proxy_tcp_port}")

        new_host = self.ui.safe_input(
            f"输入新主机地址 (回车保持 {self.config.proxy_hostname}): ",
            allow_empty=True,
        )
        if new_host is None:
            return
        host = new_host if new_host else self.config.proxy_hostname

        port_input = self.ui.safe_input(
            f"输入新端口 (回车保持 {self.config.proxy_tcp_port}): ",
            allow_empty=True,
        )
        if port_input is None:
            return
        port = port_input if port_input else self.config.proxy_tcp_port

        is_valid, error = check_proxy_values(host, port, True)
        if not is_valid:
            print(f"\n❌ {error}")
            self.ui.pause()
            return

        port_int = int(port)

        success, error_msg = self.proxy_service.save_proxy_config(
            hostname=host, port=port_int, use_proxy=True
        )

        if success:
            print(f"\n✅ 代理已更新并保存: {host}:{port}")

            if self.proxy_service.check_proxy_reachable():
                print("✅ 新地址连接正常")
            else:
                print("⚠️ 新地址无法连接，请检查代理软件是否运行")
        else:
            print(f"\n❌ 保存失败: {error_msg}")
            print("💡 配置未更改")

        self.ui.pause()

    def _test_proxy_port(self) -> None:
        """仅测试端口连通性"""
        print(f"\n🔍 测试端口连通性: {self.config.proxy_hostname}:{self.config.proxy_tcp_port}")

        is_reachable = self.proxy_service.check_proxy_reachable(timeout=3.0)

        if is_reachable:
            print("✅ 端口可达！代理软件正在运行")
        else:
            print("❌ 端口不可达！可能原因：")
            print("   1. 代理软件未启动")
            print("   2. 代理端口配置错误")
            print("   3. 防火墙阻止连接")

        self.ui.pause()

    def _test_proxy_http(self) -> None:
        """深度测试：通过代理访问 Twitter"""
        if not self.config.use_proxy:
            print("\n❌ 请先开启代理")
            self.ui.pause()
            return

        requests = _get_requests()
        if not requests:
            print("\n❌ 深度测试需要 requests 库")
            print("💡 安装命令: pip install requests")
            self.ui.pause()
            return

        print("\n🔍 深度测试: 通过代理访问 Twitter API")
        print(f"代理: {self.config.proxy_hostname}:{self.config.proxy_tcp_port}")

        proxies = {
            "http": f"http://{self.config.proxy_hostname}:{self.config.proxy_tcp_port}",
            "https": f"http://{self.config.proxy_hostname}:{self.config.proxy_tcp_port}",
        }

        test_urls = [
            ("Twitter API", "https://api.twitter.com/1.1/account/verify_credentials.json"),
            ("Twitter 主页", "https://twitter.com"),
        ]

        for name, url in test_urls:
            try:
                print(f"\n测试 {name}...", end=" ")
                resp = requests.get(url, proxies=proxies, timeout=10, verify=False)
                if resp.status_code in [200, 400, 401, 403]:
                    print(f"✅ 成功 (状态码: {resp.status_code})")
                else:
                    print(f"⚠️ 响应异常 (状态码: {resp.status_code})")
            except requests.exceptions.ProxyError:
                print("❌ 代理连接失败")
                print("   请检查代理软件是否运行")
                break
            except requests.exceptions.ConnectTimeout:
                print("❌ 连接超时")
                print("   请检查网络连接")
                break
            except Exception as e:
                print(f"❌ 测试失败: {e}")

        print()
        self.ui.pause()


__all__ = ["ProxyMenu"]
