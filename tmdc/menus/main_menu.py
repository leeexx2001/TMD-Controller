# -*- coding: utf-8 -*-
"""
主菜单模块

提供主菜单的实现。
"""

# 标准库
from typing import TYPE_CHECKING, Callable, List, Optional, Tuple

# 本地模块
from ..constants import VERSION
from .base_menu import BaseMenu

# 第三方库（无）


if TYPE_CHECKING:
    from pathlib import Path

    from ..parsers.log_parser import TMDLogParser
    from ..tmd_types import (
        IConfig,
        ICookieService,
        IDatabaseService,
        IDownloadService,
        ILogger,
        IProxyService,
        IUIHelper,
    )


class MainMenu(BaseMenu):
    """
    主菜单类

    提供主菜单的完整实现。

    Attributes:
        ui: UI 辅助实例
        logger: 日志实例
        config: 配置实例
        download_service: 下载服务实例
        database_service: 数据库服务实例
        cookie_service: Cookie 服务实例
        proxy_service: 代理服务实例
    """

    def __init__(
        self,
        ui: "IUIHelper",
        logger: "ILogger",
        config: "IConfig",
        download_service: "IDownloadService",
        database_service: "IDatabaseService",
        cookie_service: "ICookieService",
        proxy_service: "IProxyService",
        *,
        executable_path: Optional["Path"] = None,
        config_exists: bool = False,
        log_parser: Optional["TMDLogParser"] = None,
        menu_handlers: Optional[dict] = None,
    ) -> None:
        """
        初始化主菜单

        Args:
            ui: UI 辅助实例
            logger: 日志实例
            config: 配置实例
            download_service: 下载服务实例
            database_service: 数据库服务实例
            cookie_service: Cookie 服务实例
            proxy_service: 代理服务实例
            executable_path: TMD 可执行文件路径
            config_exists: 配置文件是否存在
            log_parser: 日志解析器实例
            menu_handlers: 其他菜单处理器字典
        """
        super().__init__(ui, logger, config)
        self.download_service = download_service
        self.database_service = database_service
        self.cookie_service = cookie_service
        self.proxy_service = proxy_service
        self.executable_path = executable_path
        self.config_exists = config_exists
        self.log_parser = log_parser
        self.menu_handlers = menu_handlers or {}

    def get_title(self) -> str:
        """获取菜单标题"""
        return "Twitter Media Downloader Controller"

    def get_options(self) -> List[Tuple[str, str, str]]:
        """获取菜单选项"""
        return [
            ("1", "快捷输入", "智能识别URL/用户名/列表ID开始下载"),
            ("2", "高级选项", "精确控制、批量、文件、组合、时间戳管理"),
            ("R", "恢复下载", "续传未完成任务"),
            ("Q", "快速下载", "顺序下载所有配置的固定列表"),
            ("C", "配置向导", "配置 TMD 核心参数"),
            ("L", "查看日志", "查看 TMD 运行日志"),
            ("H", "帮助", "查看帮助信息"),
            ("0", "退出", "退出程序"),
        ]

    def get_handler(self, key: str) -> Optional[Callable[[], None]]:
        """获取选项处理器"""
        handlers = {
            "1": self._menu_quick_download,
            "2": self._get_menu_handler("advanced"),
            "R": self._get_menu_handler("resume"),
            "Q": self._download_all_quick_lists,
            "C": self._get_menu_handler("config"),
            "L": self._get_menu_handler("logs"),
            "H": self._get_menu_handler("help"),
        }
        return handlers.get(key)

    def _get_menu_handler(self, menu_name: str) -> Optional[Callable[[], None]]:
        """获取其他菜单的处理器"""
        return self.menu_handlers.get(menu_name)

    def show(self) -> None:
        """
        显示主菜单

        重写基类的 show 方法，实现主菜单的特殊显示逻辑。
        """
        self.ui.clear_screen()

        while True:
            self._print_menu()

            choice = self.ui.safe_input("\n请选择: ", allow_empty=True)
            if choice is None:
                self.ui.clear_screen()
                continue
            choice = choice.upper()

            if choice == "0":
                return

            handler = self.get_handler(choice)
            if handler:
                handler()
                self.ui.clear_screen()
            else:
                self.ui.clear_screen()

    def _print_menu(self) -> None:
        """打印主菜单"""
        print(f"\n{'=' * 62}")
        print(f"Twitter Media Downloader Controller v{VERSION}".center(62))
        print("=" * 62)

        self._print_status()

        self.ui.print_menu_option("1", "快捷输入", "智能识别URL/用户名/列表ID开始下载")
        self.ui.print_menu_option("2", "高级选项", "精确控制、批量、文件、组合、时间戳管理")
        print()
        self.ui.print_menu_option("R", "恢复下载", "续传未完成任务")
        self.ui.print_menu_option("Q", "快速下载", "顺序下载所有配置的固定列表")
        print()
        print("  [C] 配置向导  [L] 查看日志  [H] 帮助  [0] 退出")
        print()
        self.ui.print_separator()

    def _print_status(self) -> None:
        """打印状态栏"""
        exe_display = str(self.executable_path) if self.executable_path else "[未找到]"
        self.ui.print_status_line("可执行文件", exe_display)
        self.ui.print_status_line("配置文件", str(self.config.config_file))

        # 显示核心配置状态
        if self.config.auth_token and self.config.ct0 and self.config.root_path:
            status = "[已配置] ✅"
        else:
            status = "[未配置 - 请运行 C] ❌"
        self.ui.print_status_line("状态", status)

        # 显示备用账号状态
        cookies = self.cookie_service.load_additional_cookies()
        cookie_count = len(cookies)
        if cookie_count > 0:
            cookie_status = f"🍪 {cookie_count}个备用"
        else:
            cookie_status = "无备用账号"
        self.ui.print_status_line("备用账号", f"[{cookie_status}]")

        # 显示固定列表状态
        if self.config.quick_list_ids:
            count = len(self.config.quick_list_ids)
            self.ui.print_status_line("固定列表", f"共{count}个列表")
        else:
            self.ui.print_status_line("固定列表", "[未配置]")

        # 显示文件分批状态
        delays = []
        if self.config.is_batch_delay_success_enabled:
            delays.append(
                f"成功延迟:{self.config.batch_delay_success_min}-{self.config.batch_delay_success_max}s"
            )
        if self.config.is_batch_delay_fail_enabled:
            delays.append(
                f"失败延迟:{self.config.batch_delay_fail_min}-{self.config.batch_delay_fail_max}s"
            )
        if delays:
            batch_value = f"{self.config.file_batch_size}行/批 [{', '.join(delays)}]"
        else:
            batch_value = f"{self.config.file_batch_size}行/批 [延迟保护:禁用]"
        self.ui.print_status_line("文件分批", batch_value)

        # 显示代理状态
        if self.config.use_proxy:
            proxy_status = self.proxy_service.get_status()
            proxy_value = f"{proxy_status.address} [{'🟢' if proxy_status.is_reachable else '🔴'} 开启]"
        else:
            proxy_value = "[⚪ 关闭]"
        self.ui.print_status_line("代理设置", proxy_value)
        print()

    def _menu_quick_download(self) -> None:
        """快捷输入模式"""
        from ..parsers.input_parser import InputParser

        self.ui.clear_screen()
        self.ui.show_header("快捷输入模式")

        print("支持格式: URL、@用户名、列表ID、Name(username)")
        print("提示: 每行输入一个目标，空回车开始下载，输入0退出\n")

        if not self._check_config_or_return(show_pause=False, check_config_exists=True):
            self.ui.pause()
            return

        while True:
            collected_items: List[Tuple[str, str]] = []
            seen: set = set()

            first_input = True
            while True:
                prompt = f"[U] ({len(collected_items)}项) > " if collected_items else "[U] > "
                user_input = self.ui.safe_input(prompt, allow_empty=True, flush_before=first_input)
                first_input = False
                if user_input is None:
                    continue

                if user_input.upper() in ("0", "M", "Q", "EXIT", "QUIT"):
                    return

                if not user_input.strip():
                    if not collected_items:
                        print("⚠️ 尚未输入任何目标")
                        continue
                    break

                input_type, value, original = InputParser.parse(user_input)

                if input_type == "unknown":
                    print(f"  ⚠️ 无法识别: {user_input}")
                elif input_type == "user":
                    if value.lower() not in seen:
                        collected_items.append(("user", value))
                        seen.add(value.lower())
                        print(f"  ✓ 用户: @{value}")
                    else:
                        print(f"  ○ 已存在: @{value}")
                elif input_type == "list":
                    if value not in seen:
                        collected_items.append(("list", value))
                        seen.add(value)
                        print(f"  ✓ 列表: {value}")
                    else:
                        print(f"  ○ 已存在: {value}")
                elif input_type == "numeric_id":
                    if value not in seen:
                        collected_items.append(("numeric_id", value))
                        seen.add(value)
                        print(f"  ✓ 数字ID: {value}")
                    else:
                        print(f"  ○ 已存在: {value}")
                elif input_type == "batch":
                    items = InputParser.parse_batch(user_input)
                    for item_type, item_value in items:
                        if item_value.lower() not in seen:
                            collected_items.append((item_type, item_value))
                            seen.add(item_value.lower())
                            print(f"  ✓ 用户: @{item_value}")
                        else:
                            print(f"  ○ 已存在: @{item_value}")

            users: List[str] = []
            lists: List[str] = []
            for item_type, item_value in collected_items:
                if item_type == "numeric_id":
                    from ..utils.validators.timestamp import handle_numeric_id_ambiguity

                    resolved_type, resolved_value = handle_numeric_id_ambiguity(item_value, self.ui)
                    if not resolved_type:
                        print(f"  ⊘ 已跳过数字 ID: {item_value}")
                        continue
                    item_type, item_value = resolved_type, resolved_value

                if item_type == "user":
                    users.append(item_value)
                elif item_type == "list":
                    lists.append(item_value)

            print(f"\n📥 开始下载 {len(users)} 个用户, {len(lists)} 个列表")
            print("-" * 62)

            result = self.download_service.download_batch(users=users, lists=lists)

            print(
                f"\n{result.get_success_message() if result.success else result.get_error_message()}"
            )

            if result.warn_users:
                print(
                    f"⚠️ 警告用户 ({len(result.warn_users)} 个): {', '.join(result.warn_users[:5])}"
                )

            print("\n" + "-" * 62)

    def _download_all_quick_lists(self) -> None:
        """顺序下载所有固定列表"""
        if not self.config.quick_list_ids:
            print("\n❌ 尚未配置固定列表！")
            self.ui.pause()
            return

        list_count = len(self.config.quick_list_ids)
        interval = self.config.quick_list_interval

        self.ui.clear_screen()
        self.ui.show_header("顺序下载所有固定列表")

        print(f"📝 将按顺序下载 {list_count} 个固定列表")
        print(f"💡 列表间将自动间隔 {interval} 秒，防止触发限流\n")

        failed_lists = []
        all_failed_users = []

        for i, list_id in enumerate(self.config.quick_list_ids, 1):
            print(f"\n{'=' * 60}")
            print(f"[{i}/{list_count}] 正在下载: {list_id}")
            print("=" * 60)

            success, failed_users = self._download_quick_list(
                list_id, batch_mode=True, show_progress=(i, list_count)
            )

            if not success:
                failed_lists.append(list_id)
                print(f"\n⚠️ 列表 {list_id} 下载失败")

            if failed_users:
                all_failed_users.extend(failed_users)

            # 列表间间隔
            if i < list_count and interval > 0:
                self.ui.delay(seconds=interval, message=f"\n⏸️ 等待 {interval} 秒后继续...", allow_skip=True)

        all_failed_users = list(set(all_failed_users))

        print()
        print("=" * 62)
        print("下载完成汇总".center(62))
        print("=" * 62)

        if failed_lists:
            print(f"📝 已完成所有列表，其中 {len(failed_lists)} 个失败:")
            for lid in failed_lists:
                print(f"  - {lid}")
        else:
            print(f"✅ 所有 {list_count} 个列表下载完成！")

        if all_failed_users:
            print(f"\n⚠️ 共有 {len(all_failed_users)} 个用户下载失败:")
            for user in all_failed_users[:10]:
                print(f"  - {user}")
            if len(all_failed_users) > 10:
                print(f"  ... 还有 {len(all_failed_users) - 10} 个")
            print("\n💡 可使用 [R] 恢复下载 重试失败的用户")

        self.ui.pause()

    def _download_quick_list(
        self,
        list_id: str,
        batch_mode: bool = False,
        show_progress: Optional[Tuple[int, int]] = None,
    ) -> Tuple[bool, List[str]]:
        """
        执行固定列表下载

        Args:
            list_id: 列表 ID
            batch_mode: 是否批量模式
            show_progress: 进度显示 (当前, 总数)

        Returns:
            (是否成功, 失败用户列表)
        """
        if not self._check_config_or_return(show_pause=not batch_mode, check_config_exists=True):
            return False, []

        if not batch_mode:
            self.ui.clear_screen()
            self.ui.show_header("固定列表下载")

        if show_progress:
            current, total = show_progress
            print(f"📝 正在下载列表 {current}/{total}: {list_id}")
        else:
            print(f"📝 正在下载列表 ID: {list_id}")

        print("⚠️ 大型列表可能需要很长时间！")
        print("💡 按 Ctrl+C 可安全暂停\n")

        result = self.download_service.download_list(list_id)

        if result.success:
            print(result.get_success_message())
        else:
            print(result.get_error_message())
            print("📝 可随时恢复 - 已下载的文件是安全的")
            print("💡 使用 [R] 恢复下载 可续传未完成任务")
            if not batch_mode:
                self.ui.pause()

        return result.success, result.warn_users
