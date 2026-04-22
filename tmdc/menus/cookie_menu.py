# -*- coding: utf-8 -*-
"""
Cookie 管理菜单模块

从 cookie_service.py 迁移 UI 交互逻辑。
提供备用账号管理的菜单界面。

主要功能：
- 查看备用账号列表
- 手动添加账号
- 智能导入 Cookie
- 删除账号
- 启用/禁用账号
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..services.cookie_service import CookieService
    from ..tmd_types import IConfig, ILogger, IUIHelper

from ..constants import Constants
from ..utils.validators.cookie import parse_cookie_string
from ..utils.formatters import mask_token
from .base_menu import BaseMenu


class CookieMenu(BaseMenu):
    """Cookie 管理菜单。

    提供备用账号管理的菜单界面。

    Attributes:
        ui: UI 辅助实例
        logger: 日志实例
        config: 配置实例
        cookie_service: Cookie 服务实例

    Example:
        >>> from tmdc.menus.cookie_menu import CookieMenu
        >>> menu = CookieMenu(ui, logger, config, cookie_service)
        >>> menu.show(config_exists=True)
    """

    ICON_COOKIE = "🍪"

    def __init__(
        self,
        ui: "IUIHelper",
        logger: "ILogger",
        config: "IConfig",
        cookie_service: "CookieService",
        config_exists: bool = False,
    ) -> None:
        """初始化 Cookie 管理菜单。

        Args:
            ui: UI 辅助实例
            logger: 日志实例
            config: 配置实例
            cookie_service: Cookie 服务实例
            config_exists: 主账号是否已配置
        """
        super().__init__(ui, logger, config)
        self.cookie_service = cookie_service
        self.config_exists = config_exists

    def show(self) -> None:
        """显示 Cookie 管理菜单。"""
        while True:
            cookies = self.cookie_service.load_additional_cookies()

            disabled_flag = self.config.cookie_file.with_suffix(".yaml.disabled")
            is_disabled = disabled_flag.exists() and not self.config.cookie_file.exists()

            main_status = "已配置" if self.config_exists else "未配置"
            if is_disabled:
                actual_count = len(cookies) if cookies else 0
                cookie_status = f"{actual_count} 个 [⚠️ 已暂时禁用]"
            else:
                cookie_status = f"{len(cookies)} 个"

            status_lines = [
                ("主账号状态", main_status, ""),
                ("备用账号数", cookie_status, ""),
            ]

            if not is_disabled and cookies:
                status_lines.append(("轮询状态", f"{self.ICON_COOKIE} 已启用轮询下载", ""))

            status_lines.append(("文件位置", str(self.config.cookie_file), ""))

            options = [
                ("1", "添加新账号", "手动输入 auth_token 和 ct0"),
                ("2", "智能导入", "粘贴浏览器 Cookie 字符串自动提取"),
                ("3", "查看账号", "脱敏显示所有备用账号"),
                ("4", "删除账号", "移除不需要的账号"),
                (
                    "5",
                    "恢复启用" if is_disabled else "暂时禁用",
                    "重新启用备用账号轮询" if is_disabled else "临时停用但不删除账号数据",
                ),
                ("0", "返回上级菜单", ""),
            ]

            hints = []
            if is_disabled:
                hints.append("当前备用账号已被暂时禁用，下载时将不使用轮询")
            else:
                hints.append("备用账号仅用于提升下载速度")

            self._renderer.render_menu(
                title="备用账号管理（突破限速）",
                options=options,
                status_lines=status_lines,
                hints=hints,
            )

            choice = self._get_menu_choice()

            if choice == "0":
                break
            elif choice == "1":
                if is_disabled:
                    print("\n❌ 请先使用 [5] 启用账号后再添加")
                    self.ui.pause()
                else:
                    self._add_cookie_manual()
            elif choice == "2":
                if is_disabled:
                    print("\n❌ 请先使用 [5] 启用账号后再导入")
                    self.ui.pause()
                else:
                    self._add_cookie_smart()
            elif choice == "3":
                self._list_cookies()
                if is_disabled:
                    print(f"\n⚠️ 当前状态: 已暂时禁用（共 {len(cookies)} 个）")
                self.ui.pause()
            elif choice == "4":
                if is_disabled:
                    print("\n❌ 请先使用 [5] 启用账号后再删除")
                    self.ui.pause()
                else:
                    self._delete_cookie()
            elif choice == "5":
                self._toggle_cookies_disabled()

    def _toggle_cookies_disabled(self) -> None:
        """切换备用账号的启用/禁用状态"""
        result = self.cookie_service.toggle_cookies_disabled()
        if result.success:
            print(f"\n✅ {result.message}")
        else:
            print(f"\n❌ {result.error}")
        self.ui.pause()

    def _add_cookie_manual(self) -> None:
        """手动添加账号"""
        print("\n💡 请从浏览器获取备用账号的 Cookie")
        print("注意: 备用账号不需要关注任何人，仅用于下载提速")
        print("      建议添加 2-3 个小号，可显著提升大列表下载速度\n")

        auth_token = self.ui.safe_input("输入 auth_token: ")
        if auth_token is None:
            return
        if not auth_token:
            print("❌ auth_token 不能为空")
            self.ui.pause()
            return

        ct0 = self.ui.safe_input("输入 ct0: ")
        if ct0 is None:
            return
        if not ct0:
            print("❌ ct0 不能为空")
            self.ui.pause()
            return

        self._save_new_cookie(auth_token, ct0)

    def _add_cookie_smart(self) -> None:
        """智能导入 Cookie 字符串"""
        print("\n💡 智能导入：请从浏览器直接复制完整的 Cookie 字符串")
        print("支持格式: document.cookie 内容 或 Request Headers 中的 Cookie 字段")
        print("示例: auth_token=xxx; ct0=yyy; ...")
        print("按 Ctrl+V 粘贴，完成后按回车\n")

        cookie_str = self.ui.safe_input("粘贴 Cookie: ")
        if cookie_str is None:
            return
        if not cookie_str:
            print("❌ 未输入任何内容")
            self.ui.pause()
            return

        if len(cookie_str) < Constants.COOKIE_MIN_LEN:
            print("❌ 输入过短，未检测到有效 Cookie")
            self.ui.pause()
            return

        parsed = parse_cookie_string(cookie_str)

        if not parsed:
            print("❌ 未能从字符串中提取到 auth_token 和 ct0")
            print("💡 请确保包含完整的 auth_token 和 ct0 字段")
            self.ui.pause()
            return

        print("\n📝 解析成功：")
        self.ui.print_status_line("auth_token", mask_token(parsed['auth_token']))
        self.ui.print_status_line("ct0", mask_token(parsed['ct0']))

        if self.ui.confirm_action("确认添加此账号? [y/N]", explicit=True):
            self._save_new_cookie(parsed["auth_token"], parsed["ct0"])

    def _save_new_cookie(self, auth_token: str, ct0: str) -> None:
        """保存新账号"""
        success, error = self.cookie_service.add_cookie(auth_token, ct0)
        if success:
            cookies = self.cookie_service.load_additional_cookies()
            print("\n✅ 已添加备用账号")
            print(f"📝 当前共有 {len(cookies)} 个备用账号")
            print("💡 下次下载时将自动轮询使用这些账号")
        else:
            print(f"\n❌ 添加失败: {error}")

        self.ui.pause()

    def _list_cookies(self) -> None:
        """查看所有备用账号（脱敏）"""
        cookies = self.cookie_service.load_additional_cookies()

        if not cookies:
            print("📝 暂无备用账号")
            return

        print(f"\n当前共有 {len(cookies)} 个备用账号:")
        print(f"{'序号':<4} {'auth_token':<20} {'ct0':<15}")
        print("-" * 45)

        for i, cookie in enumerate(cookies, 1):
            token = cookie.get("auth_token", "unknown")
            ct0 = cookie.get("ct0", "unknown")
            masked_token = mask_token(token)
            masked_ct0 = mask_token(ct0)
            print(f"[{i}]  {masked_token:<20} {masked_ct0:<15}")

        print("\n📝 脱敏显示规则: 前6位...后4位")

    def _delete_cookie(self) -> None:
        """删除备用账号"""
        cookies = self.cookie_service.load_additional_cookies()

        if not cookies:
            print("📝 暂无备用账号可删除")
            self.ui.pause()
            return

        self._list_cookies()
        print()

        choice = self.ui.safe_input("请输入要删除的序号 (或回车取消): ", allow_empty=True)
        if choice is None or not choice.isdigit():
            return

        idx = int(choice) - 1
        if 0 <= idx < len(cookies):
            masked = mask_token(cookies[idx].get("auth_token", ""))
            if self.ui.confirm_action(
                f"确认删除账号 {masked}? [y/N]",
                explicit=True,
            ):
                success, error, removed = self.cookie_service.remove_cookie(idx)
                if success and removed:
                    print(f"\n✅ 已删除账号: {mask_token(removed.get('auth_token', ''))}")
                    remaining = self.cookie_service.load_additional_cookies()
                    print(f"📝 剩余 {len(remaining)} 个备用账号")
                else:
                    print(f"\n❌ 删除失败: {error}")
                    print("💡 配置未更改")
            else:
                print("📝 已取消删除")
        else:
            print("❌ 无效的序号")

        self.ui.pause()


__all__ = ["CookieMenu"]
