# -*- coding: utf-8 -*-
"""
配置菜单模块

提供配置向导功能，包括 TMD 核心配置、多账号管理、代理管理等。

主要功能：
- TMD 核心配置（auth_token/ct0/root_path）
- 多账号 Cookie 管理
- 代理设置管理
- 固定列表管理
- 文件下载设置
- 列表间间隔设置
- 路径迁移
"""

from __future__ import annotations

# 标准库
import os
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    import logging

    from ..services.cookie_service import CookieService
    from ..services.proxy_service import ProxyService
    from ..tmd_types import IConfig, IDatabaseService, IDownloadService, IUIHelper

# 第三方库（无）

# 本地模块
from ..config.config import TMDConfig
from ..constants import C
from ..parsers import DelayParser
from ..utils.formatters import mask_token
from ..utils.validators.cookie import parse_cookie_string
from ..utils.validators.auth import validate_auth_token, validate_ct0
from .base_menu import BaseMenu


class ConfigMenu(BaseMenu):
    """
    配置菜单

    提供配置向导功能，管理 TMD 核心配置、多账号、代理等设置。

    Attributes:
        ui: UI 辅助实例
        logger: 日志实例
        config: 配置实例
        cookie_service: Cookie 服务实例
        proxy_service: 代理服务实例
        config_exists: 配置是否已存在

    Example:
        >>> from tmdc.menus.config_menu import ConfigMenu
        >>> menu = ConfigMenu(ui, logger, config, cookie_service, proxy_service)
        >>> menu.show()
    """

    def __init__(
        self,
        ui: "IUIHelper",
        logger: "logging.Logger",
        config: "IConfig",
        cookie_service: "CookieService",
        proxy_service: "ProxyService",
        download_service: "IDownloadService",
        database_service: "IDatabaseService",
    ) -> None:
        """
        初始化配置菜单

        Args:
            ui: UI 辅助实例
            logger: 日志实例
            config: 配置实例
            cookie_service: Cookie 服务实例
            proxy_service: 代理服务实例
            download_service: 下载服务实例
            database_service: 数据库服务实例
        """
        super().__init__(ui, logger, config)
        self.cookie_service = cookie_service
        self.proxy_service = proxy_service
        self.download_service = download_service
        self.database_service = database_service
        self.config_exists: bool = bool(config.auth_token and config.ct0 and config.root_path)

    # ==================== 公共接口 ====================

    def show(self) -> None:
        """
        显示配置向导菜单（整合版 - v4.8.0 直接管理 TMD 核心配置）
        """
        options = [
            ("1", "TMD核心配置", "auth_token/ct0/root_path（运行必需）"),
            ("2", "多账号管理", "多Cookie轮询（突破限速）"),
            ("3", "代理管理", "代理设置与连通性测试"),
            ("4", "固定列表管理", "配置常用列表ID（配合 [Q] 快速下载）"),
            ("5", "文件下载设置", "分批大小、双轨风控延迟"),
            ("6", "列表间间隔", "设置 [Q] 键批量下载时的间隔"),
            ("7", "迁移路径", "修改数据库中的下载路径（移动文件夹后使用）"),
            ("0", "返回主菜单", ""),
        ]

        handlers = {
            "1": self._config_tmd_core,
            "2": self._show_cookie_menu,
            "3": self._show_proxy_menu,
            "4": self._show_quick_list_menu,
            "5": self._config_file_batch_settings,
            "6": self._config_quick_list_interval,
            "7": self._show_path_menu,
        }

        while True:
            self.ui.clear_screen()
            self.ui.show_header("配置向导")

            # 状态显示
            self.ui.print_status_line("TMD核心", self._get_core_status())
            self.ui.print_status_line("备用账号", self._get_cookie_status())
            self.ui.print_status_line("代理设置", self._get_proxy_status())
            self.ui.print_status_line("文件分批", f"{self.config.file_batch_size} 行/批")
            self.ui.print_status_line("风控延迟", self._get_delay_status())
            self.ui.print_status_line("下载线程", self._get_routine_status())
            self.ui.print_status_line("固定列表", self._get_quick_list_status())
            self.ui.print_status_line("列表间隔", self._get_interval_status())

            self.ui.print_separator()
            for key, label, desc in options:
                self.ui.print_menu_option(key, label, desc)
            self.ui.print_separator()

            choice = self._get_menu_choice("请选择 [0-7]")

            if choice == "0":
                break

            handler = handlers.get(choice)
            if handler:
                handler()
            else:
                continue

    def _show_cookie_menu(self) -> None:
        """显示Cookie菜单"""
        from .cookie_menu import CookieMenu

        cookie_menu = CookieMenu(
            self.ui, self.logger, self.config, self.cookie_service, self.config_exists
        )
        cookie_menu.show()

    def _show_proxy_menu(self) -> None:
        """显示代理菜单"""
        from .proxy_menu import ProxyMenu

        proxy_menu = ProxyMenu(self.ui, self.logger, self.config, self.proxy_service)
        proxy_menu.show()

    def _show_quick_list_menu(self) -> None:
        """显示固定列表菜单"""
        from .quick_list_menu import QuickListMenu

        quick_list_menu = QuickListMenu(
            self.ui,
            self.logger,
            self.config,
            self.download_service,
            self.database_service,
        )
        quick_list_menu.show()

    def _show_path_menu(self) -> None:
        """显示路径菜单"""
        from .path_menu import PathMenu

        path_menu = PathMenu(self.ui, self.logger, self.config, self.database_service)
        path_menu.show()

    # ==================== 私有方法：状态显示 ====================

    def _get_core_status(self) -> str:
        """获取 TMD 核心状态"""
        if self.config.auth_token and self.config.ct0 and self.config.root_path:
            token_valid, _ = validate_auth_token(self.config.auth_token)
            ct0_valid, _ = validate_ct0(self.config.ct0)
            if token_valid and ct0_valid:
                return "已配置"
            else:
                return "格式异常"
        else:
            missing = []
            if not self.config.auth_token:
                missing.append("auth_token")
            if not self.config.ct0:
                missing.append("ct0")
            if not self.config.root_path:
                missing.append("root_path")
            return f"缺少: {', '.join(missing)}"

    def _get_cookie_status(self) -> str:
        """获取备用账号状态"""
        cookie_count = len(self.cookie_service.load_additional_cookies())
        disabled_flag = self.config.cookie_file.with_suffix(".yaml.disabled")
        if disabled_flag.exists():
            return f"{cookie_count}个 [已禁用]"
        elif cookie_count > 0:
            return f"{cookie_count}个 [已启用]"
        else:
            return "未配置"

    def _get_proxy_status(self) -> str:
        """获取代理设置状态"""
        proxy_status = "开启" if self.config.use_proxy else "关闭"
        return f"{self.config.proxy_hostname}:{self.config.proxy_tcp_port} [{proxy_status}]"

    def _get_delay_status(self) -> str:
        """获取风控延迟状态"""
        delays = []
        if self.config.is_batch_delay_success_enabled:
            delays.append(
                f"成功:{self.config.batch_delay_success_min}-{self.config.batch_delay_success_max}s"
            )
        if self.config.is_batch_delay_fail_enabled:
            delays.append(
                f"失败:{self.config.batch_delay_fail_min}-{self.config.batch_delay_fail_max}s"
            )
        return ", ".join(delays) if delays else "禁用"

    def _get_routine_status(self) -> str:
        """获取下载线程状态"""
        return (
            "自动(CPUx10)"
            if self.config.max_download_routine == 0
            else f"{self.config.max_download_routine}线程"
        )

    def _get_quick_list_status(self) -> str:
        """获取固定列表状态"""
        list_count = len(self.config.quick_list_ids)
        return f"已配置 {list_count} 个" if list_count > 0 else "未配置"

    def _get_interval_status(self) -> str:
        """获取列表间间隔状态"""
        return (
            f"{self.config.quick_list_interval}秒"
            if self.config.quick_list_interval > 0
            else "禁用"
        )

    # ==================== 私有方法：TMD 核心配置 ====================

    def _config_tmd_core(self) -> None:
        """
        TMD 核心配置（v4.8.0 重写：直接管理替代 --conf）
        """
        while True:
            self.ui.clear_screen()
            self.ui.show_header("TMD 核心配置")

            # auth_token 状态
            self._display_auth_token_status()

            # ct0 状态
            self._display_ct0_status()

            # root_path
            self._display_root_path_status()

            # max_download_routine
            self._display_max_routine_status()

            self.ui.print_separator()

            # 操作选项
            self.ui.print_menu_option("1", "修改 Cookie", "同时设置 auth_token 和 ct0")
            self.ui.print_menu_option("2", "修改下载路径", "媒体文件保存位置")
            self.ui.print_menu_option("3", "修改下载线程数", "并发下载数量（0=自动计算）")
            self.ui.print_menu_option("4", "智能导入", "粘贴浏览器 Cookie 字符串自动提取")
            self.ui.print_menu_option("0", "返回上级菜单", "")
            print("提示: 从浏览器开发者工具获取 auth_token 和 ct0")
            print("       修改后立即生效，无需重启程序")

            self.ui.flush_keyboard_buffer()
            input_str = self.ui.safe_input("\n请选择 [1-4,0]: ")
            choice = input_str.strip().upper() if input_str else ""

            if choice == "0":
                # 退出前检查配置完整性
                if not self.config.auth_token or not self.config.ct0 or not self.config.root_path:
                    print("\n 警告: 核心配置尚未完成，可能无法正常运行")
                    self.ui.pause()
                break
            elif choice == "1":
                self._edit_cookie()
            elif choice == "2":
                self._edit_root_path()
            elif choice == "3":
                self._edit_max_download_routine()
            elif choice == "4":
                self._smart_import_cookie()
            else:
                continue

    def _display_auth_token_status(self) -> None:
        """显示 auth_token 状态"""
        if self.config.auth_token:
            valid, err = validate_auth_token(self.config.auth_token)
            status = "有效" if valid else err
            masked = mask_token(self.config.auth_token)
            self.ui.print_status_line("auth_token", masked, status)
        else:
            self.ui.print_status_line("auth_token", "[未配置]")

    def _display_ct0_status(self) -> None:
        """显示 ct0 状态"""
        if self.config.ct0:
            valid, err = validate_ct0(self.config.ct0)
            status = "有效" if valid else err
            masked = mask_token(self.config.ct0)
            self.ui.print_status_line("ct0", masked, status)
        else:
            self.ui.print_status_line("ct0", "[未配置]")

    def _display_root_path_status(self) -> None:
        """显示下载路径状态"""
        if self.config.root_path:
            expanded = str(Path(self.config.root_path).expanduser())
            exists = "" if Path(expanded).exists() else "(不存在，将自动创建)"
            self.ui.print_status_line("下载路径", expanded, exists)
        else:
            self.ui.print_status_line("下载路径", "[未配置]")

    def _display_max_routine_status(self) -> None:
        """显示下载线程状态"""
        if self.config.max_download_routine == 0:
            routine_desc = "自动 (CPUx10, 封顶100)"
        else:
            routine_desc = f"{self.config.max_download_routine} 线程"
        self.ui.print_status_line("下载线程", routine_desc)
        print()

    # ==================== 私有方法：编辑功能 ====================

    def _edit_cookie(self) -> None:
        """编辑 Cookie（同时设置 auth_token 和 ct0）"""
        print(
            f"\n当前 auth_token: {mask_token(self.config.auth_token) if self.config.auth_token else '未配置'}"
        )
        print(
            f"当前 ct0:        {mask_token(self.config.ct0) if self.config.ct0 else '未配置'}"
        )
        print("\n请输入新的 Cookie（可分别输入 auth_token 和 ct0）：")
        print("提示: Windows 终端按 Ctrl+V 粘贴，或右键粘贴")
        print("       直接回车保持原值不变\n")

        # 输入 auth_token
        new_token = self.ui.safe_input("auth_token: ")
        if new_token is None:
            return

        # 输入 ct0
        new_ct0 = self.ui.safe_input("ct0: ")
        if new_ct0 is None:
            return

        # 如果都为空，保持原值
        if not new_token and not new_ct0:
            print("保持原值不变")
            self.ui.pause()
            return

        # 清理和验证 auth_token
        auth_token = None
        if new_token:
            new_token = new_token.strip("\"'").replace(" ", "")
            valid, error = validate_auth_token(new_token)
            if not valid:
                print(f"\n auth_token 格式错误: {error}")
                self.ui.pause()
                return
            auth_token = new_token

        # 清理和验证 ct0
        ct0 = None
        if new_ct0:
            new_ct0 = new_ct0.strip("\"'").replace(" ", "")
            valid, error = validate_ct0(new_ct0)
            if not valid:
                print(f"\n ct0 格式错误: {error}")
                self.ui.pause()
                return
            ct0 = new_ct0

        # 首次配置时允许部分保存
        allow_partial = not (self.config.auth_token and self.config.ct0 and self.config.root_path)
        success, error = self.config.save_core_config(
            auth_token=auth_token, ct0=ct0, allow_partial=allow_partial
        )
        if success:
            print("\n Cookie 已更新")
            if auth_token:
                print(f" auth_token: {mask_token(auth_token)}")
            if ct0:
                print(f" ct0:        {mask_token(ct0)}")
            # 更新 config_exists 状态
            if self.config.auth_token and self.config.ct0 and self.config.root_path:
                self.config_exists = True
        else:
            print(f"\n 保存失败: {error}")

        self.ui.pause()

    def _edit_root_path(self) -> None:
        """编辑下载路径"""
        current = self.config.root_path or ""
        print(f"\n当前下载路径: {current if current else '未配置'}")
        print("请输入新的下载路径（支持 ~ 表示用户目录，如 ~/Downloads/twitter）：")

        new_path = self.ui.safe_input("\n下载路径: ")
        if new_path is None:
            return

        if not new_path:
            print("保持原值不变")
            self.ui.pause()
            return

        # 展开 ~ 和 Windows 环境变量（如 %USERPROFILE%）为实际路径
        expanded = os.path.expandvars(str(Path(new_path).expanduser()))

        # 检查路径有效性（不要求必须存在，但要求格式合法）
        try:
            path_obj = Path(expanded)
            # 尝试创建父目录以验证权限（如果不存在）
            if not path_obj.exists():
                print(f"\n 路径不存在: {expanded}")
                print("   程序将在首次下载时自动创建该目录")
                if not self.ui.confirm_action("确认使用此路径? [y/N]", explicit=True):
                    print(" 已取消")
                    self.ui.pause()
                    return
        except Exception as e:
            print(f"\n 路径格式无效: {e}")
            self.ui.pause()
            return

        # 首次配置时允许部分保存
        allow_partial = not (self.config.auth_token and self.config.ct0 and self.config.root_path)
        success, error = self.config.save_core_config(
            root_path=new_path, allow_partial=allow_partial
        )
        if success:
            print("\n 下载路径已更新")
            print(f" 新路径: {expanded}")
            # 更新 config_exists 状态
            if self.config.auth_token and self.config.ct0 and self.config.root_path:
                self.config_exists = True
        else:
            print(f"\n 保存失败: {error}")

        self.ui.pause()

    def _edit_max_download_routine(self) -> None:
        """编辑下载线程数"""
        current = self.config.max_download_routine
        if current == 0:
            routine_desc = "0 (自动: CPUx10, 封顶100)"
        else:
            routine_desc = f"{current} 线程"

        print(f"\n当前下载线程数: {routine_desc}")
        print("请输入新的线程数（0-100）：")
        print("  0 = 自动计算（根据CPU核心数x10，封顶100）")
        print("  1-100 = 手动指定并发数（建议根据带宽调整）")

        input_val = self.ui.safe_input("\n线程数: ")
        if input_val is None:
            return

        if not input_val:
            print("保持原值不变")
            self.ui.pause()
            return

        try:
            new_val = int(input_val)
            if not (0 <= new_val <= 100):
                print(" 数值必须在 0-100 之间")
                self.ui.pause()
                return
        except ValueError:
            print(" 请输入有效的整数")
            self.ui.pause()
            return

        success, error = self.config.save_core_config(max_download_routine=new_val)
        if success:
            status = "无限制" if new_val == 0 else f"{new_val} 线程"
            print(f"\n 下载线程数已更新: {status}")
        else:
            print(f"\n 保存失败: {error}")

        self.ui.pause()

    def _smart_import_cookie(self) -> None:
        """智能导入：从浏览器 Cookie 字符串提取（复用 InputParser）"""
        print("\n 智能导入：请从浏览器直接复制完整的 Cookie 字符串")
        print("支持格式: document.cookie 内容 或 Request Headers 中的 Cookie 字段")
        print("示例: auth_token=xxx; ct0=yyy; ...")
        print("按 Ctrl+V 粘贴，完成后按回车\n")

        cookie_str = self.ui.safe_input("粘贴 Cookie: ")
        if cookie_str is None:
            return
        if not cookie_str:
            print(" 未输入任何内容")
            self.ui.pause()
            return

        if len(cookie_str) < C.COOKIE_MIN_LEN:
            print(" 输入过短，未检测到有效 Cookie")
            self.ui.pause()
            return

        parsed = parse_cookie_string(cookie_str)

        if not parsed:
            print(" 未能从字符串中提取到有效的 auth_token 和 ct0")
            print(" 请确保包含完整的 auth_token 和 ct0 字段")
            self.ui.pause()
            return

        auth_token = parsed.get("auth_token", "")
        ct0 = parsed.get("ct0", "")

        print("\n 解析成功：")
        self.ui.print_status_line("auth_token", f"{mask_token(auth_token)} ({len(auth_token)}字符)")
        self.ui.print_status_line("ct0", f"{mask_token(ct0)} ({len(ct0)}字符)")

        # 验证格式
        valid_t, err_t = validate_auth_token(auth_token)
        valid_c, err_c = validate_ct0(ct0)

        if not valid_t:
            print(f"\n  auth_token 格式异常: {err_t}")
        if not valid_c:
            print(f"\n  ct0 格式异常: {err_c}")

        if self.ui.confirm_action("确认保存这些凭据? [y/N]", explicit=True, logger=self.logger):
            # 首次配置时允许部分保存
            allow_partial = not (
                self.config.auth_token and self.config.ct0 and self.config.root_path
            )
            success, error = self.config.save_core_config(
                auth_token=auth_token, ct0=ct0, allow_partial=allow_partial
            )
            if success:
                print("\n 凭据已保存到配置文件")
                if self.config.root_path:
                    self.config_exists = True
                    print(" 核心配置已完成，可以开始下载")
                else:
                    print(" 请继续配置 [3] 下载路径")
            else:
                print(f"\n 保存失败: {error}")

        self.ui.pause()

    # ==================== 私有方法：文件下载设置 ====================

    def _config_file_batch_settings(self) -> None:
        """文件批量下载设置（双轨延迟版）"""
        while True:
            self.ui.clear_screen()
            self.ui.show_header("文件下载设置")

            # 状态显示
            self.ui.print_status_line("分批大小", f"{self.config.file_batch_size} 行/批 (范围1-50)")

            s_status = (
                f"{self.config.batch_delay_success_min}-{self.config.batch_delay_success_max}秒"
                if self.config.is_batch_delay_success_enabled
                else "禁用"
            )
            f_status = (
                f"{self.config.batch_delay_fail_min}-{self.config.batch_delay_fail_max}秒"
                if self.config.is_batch_delay_fail_enabled
                else "禁用"
            )

            self.ui.print_status_line("成功延迟", s_status)
            self.ui.print_status_line("失败延迟", f_status)
            print()

            self.ui.print_separator()

            # 操作选项
            self.ui.print_menu_option("1", "修改分批大小", "设置文件导入时的批次大小")
            self.ui.print_menu_option("2", "修改成功延迟", "批次成功后延迟（防压力）")
            self.ui.print_menu_option("3", "修改失败延迟", "批次失败后延迟（防风控）")
            self.ui.print_menu_option("0", "返回上级菜单", "")

            print(" 输入格式: 最小值 最大值（如 4 9），输入 0 0 表示禁用")
            print("       直接回车保持当前设置不变")

            self.ui.flush_keyboard_buffer()
            input_str = self.ui.safe_input("\n请选择 [1-3,0]: ")
            choice = input_str.strip().upper() if input_str else ""

            if choice == "0":
                break
            elif choice == "1":
                self._set_file_batch_size()
            elif choice == "2":
                self._set_batch_delay_success()
            elif choice == "3":
                self._set_batch_delay_fail()
            else:
                continue

    def _set_file_batch_size(self) -> None:
        """设置文件分批大小"""
        print(f"\n当前分批大小: {self.config.file_batch_size} 行/批")
        print("范围: 1-50（推荐 3-10，大文件建议调小）")

        self.ui.flush_keyboard_buffer()
        user_input = self.ui.safe_input("输入新值（直接回车保持不变）: ")
        user_input = user_input.strip() if user_input else ""

        if not user_input:
            print("保持原值不变")
            self.ui.pause()
            return

        try:
            new_size = int(user_input)
            if not (1 <= new_size <= 50):
                print(" 必须在 1-50 之间")
                self.ui.pause()
                return

            success, error = self.config.save_batch_config(new_size)
            if success:
                print(f" 分批大小已更新为 {new_size}")
            else:
                print(f" 保存失败: {error}")

        except ValueError:
            print(" 请输入有效的数字")

        self.ui.pause()

    def _set_batch_delay_success(self) -> None:
        """设置成功延迟（范围输入格式）"""
        current = (
            "禁用"
            if not self.config.is_batch_delay_success_enabled
            else f"{self.config.batch_delay_success_min} {self.config.batch_delay_success_max}"
        )
        print(f"\n当前成功延迟: {current}")
        print("说明: 每批次下载成功后，随机延迟一段时间再开始下一批")
        print("      有助于降低服务器压力（建议 2-5 秒）")
        print("输入格式: 最小值 最大值（如 2 5），输入 0 0 或 0 表示禁用")

        self.ui.flush_keyboard_buffer()
        user_input = self.ui.safe_input("输入新值（直接回车保持不变）: ")
        user_input = user_input.strip() if user_input else ""

        if not user_input:
            print("保持原值不变")
            self.ui.pause()
            return

        parsed = DelayParser.parse(user_input)
        if parsed is None:
            print(" 输入格式无效，请使用 '2 5' 或 '2-5' 格式")
            self.ui.pause()
            return

        new_min, new_max = parsed

        f_min, f_max = (
            self.config.batch_delay_fail_min,
            self.config.batch_delay_fail_max,
        )

        success, error = self.config.save_batch_delay_config(new_min, new_max, f_min, f_max)
        if success:
            if new_max == 0:
                print(" 已禁用成功延迟")
            else:
                print(f" 成功延迟已更新: {new_min}-{new_max} 秒")
                print(" 仅当批次下载成功时触发此延迟")
        else:
            print(f" 保存失败: {error}")

        self.ui.pause()

    def _set_batch_delay_fail(self) -> None:
        """设置失败延迟（范围输入格式）"""
        current = (
            "禁用"
            if not self.config.is_batch_delay_fail_enabled
            else f"{self.config.batch_delay_fail_min} {self.config.batch_delay_fail_max}"
        )
        print(f"\n当前失败延迟: {current}")
        print("说明: 某批次下载失败后，随机延迟一段时间再开始下一批")
        print("      有助于规避服务器风控（建议 5-15 秒）")
        print("输入格式: 最小值 最大值（如 5 10），输入 0 0 或 0 表示禁用")

        self.ui.flush_keyboard_buffer()
        user_input = self.ui.safe_input("输入新值（直接回车保持不变）: ")
        user_input = user_input.strip() if user_input else ""

        if not user_input:
            print("保持原值不变")
            self.ui.pause()
            return

        parsed = DelayParser.parse(user_input)
        if parsed is None:
            print(" 输入格式无效，请使用 '5 10' 或 '5-10' 格式")
            self.ui.pause()
            return

        new_min, new_max = parsed

        s_min, s_max = (
            self.config.batch_delay_success_min,
            self.config.batch_delay_success_max,
        )

        success, error = self.config.save_batch_delay_config(s_min, s_max, new_min, new_max)
        if success:
            if new_max == 0:
                print(" 已禁用失败延迟")
            else:
                print(f" 失败延迟已更新: {new_min}-{new_max} 秒")
                print(" 仅当批次下载失败时触发此延迟")
        else:
            print(f" 保存失败: {error}")

        self.ui.pause()

    # ==================== 私有方法：列表间间隔设置 ====================

    def _config_quick_list_interval(self) -> None:
        """列表间间隔设置"""
        while True:
            self.ui.clear_screen()
            self.ui.show_header("列表间间隔")

            # 状态显示
            interval_status = (
                f"{self.config.quick_list_interval}秒"
                if self.config.quick_list_interval > 0
                else "禁用"
            )
            self.ui.print_status_line("列表间隔", f"{interval_status} ([Q]键批量下载时使用)")
            print()

            self.ui.print_separator()

            # 操作选项
            self.ui.print_menu_option("1", "修改列表间隔", "设置 [Q] 键下载时的列表间延迟")
            self.ui.print_menu_option("0", "返回上级菜单", "")

            print(" 范围: 0-300 秒，0 表示禁用")
            print("       直接回车保持当前设置不变")

            self.ui.flush_keyboard_buffer()
            input_str = self.ui.safe_input("\n请选择 [1,0]: ")
            choice = input_str.strip().upper() if input_str else ""

            if choice == "0":
                break
            elif choice == "1":
                self._set_quick_list_interval()
            else:
                continue

    def _set_quick_list_interval(self) -> None:
        """设置列表间间隔"""
        current = self.config.quick_list_interval
        print(f"\n当前间隔: {current} 秒（范围 0-300，0=禁用）")

        user_input = self.ui.safe_input("新值（回车保持）: ")
        user_input = user_input.strip() if user_input else ""
        if user_input:
            try:
                val = int(user_input)
                if 0 <= val <= 300:
                    success, err = self.config.save_quick_list_interval(val)
                    print(" 已更新" if success else f" {err}")
                else:
                    print(" 超出范围")
            except ValueError:
                print(" 无效输入")
            self.ui.pause()


__all__ = ["ConfigMenu"]
