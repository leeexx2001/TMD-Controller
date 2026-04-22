# -*- coding: utf-8 -*-
"""
TMD UI 辅助模块

提供用户界面交互的辅助功能，包括：
- 屏幕清空和暂停
- 安全输入处理
- 标题头显示
- 操作确认
- 消息打印（成功/错误/警告/信息）
- 数字输入
- Token 脱敏
"""

from __future__ import annotations

# 标准库
import os
import random
import time
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from tmdc.tmd_types import ILogger, IUIHelper

# 第三方库（msvcrt 是 Windows 专用标准库，使用 try/except 处理跨平台）
try:
    import msvcrt
except ImportError:
    msvcrt = None  # type: ignore[assignment]

# 本地模块
from tmdc.constants import C
from tmdc.utils.text_utils import display_width


class UIHelper:
    """
    UI 渲染辅助类

    实现用户界面交互的标准功能，支持 headless 模式。

    Attributes:
        UI_WIDTH: UI 显示宽度
        SEPARATOR_LINE: 分隔线
        HEADER_SEPARATOR: 标题分隔线
        BATCH_MAX_DISPLAY: 批量显示数量上限
        ICON_USER: 用户图标
        ICON_LIST: 列表图标
        ICON_COOKIE: Cookie 图标
        headless_mode: 是否为无头模式

    Example:
        >>> ui = UIHelper()
        >>> ui.clear_screen()
        >>> ui.show_header("主菜单")
        >>> if ui.confirm_action("确认删除?"):
        ...     print("已删除")
    """

    UI_WIDTH: int = C.UI_WIDTH
    """UI 显示宽度"""

    SEPARATOR_LINE: str = "-" * C.UI_WIDTH
    """分隔线"""

    HEADER_SEPARATOR: str = "=" * C.UI_WIDTH
    """标题分隔线"""

    BATCH_MAX_DISPLAY: int = C.BATCH_MAX_DISPLAY
    """批量显示数量上限"""

    ICON_USER: str = "👤"
    """用户图标"""

    ICON_LIST: str = "📋"
    """列表图标"""

    ICON_COOKIE: str = "🍪"
    """Cookie 图标"""

    def __init__(self, headless_mode: bool = False) -> None:
        """
        初始化 UI 辅助实例

        Args:
            headless_mode: 是否为无头模式（无交互模式）
        """
        self.headless_mode = headless_mode

    # ==================== 核心方法 ====================

    def clear_screen(self) -> None:
        """
        清空屏幕 - Windows 专用

        清屏后自动清空键盘缓冲区，避免残留输入影响后续操作。
        """
        os.system("cls")
        self.flush_keyboard_buffer()

    def pause(self, prompt: str = "按回车键继续...") -> None:
        """
        暂停等待用户输入

        在 headless 模式下自动跳过。

        Args:
            prompt: 提示消息
        """
        if self.headless_mode:
            return
        self.flush_keyboard_buffer()
        input(f"\n{prompt}")

    def safe_input(
        self,
        prompt: str,
        *,
        allow_empty: bool = False,
        default: Optional[str] = None,
        flush_before: bool = True,
    ) -> Optional[str]:
        """
        安全输入，处理 EOFError 和 KeyboardInterrupt

        Args:
            prompt: 输入提示
            allow_empty: 是否允许空输入
            default: 默认值（空输入时返回）
            flush_before: 是否在读取前清空键盘缓冲区（仅第一次输入需要，粘贴多行时避免丢行）

        Returns:
            用户输入内容，取消返回 None，空输入且不允许空时返回 default 或空字符串

        Example:
            >>> ui = UIHelper()
            >>> name = ui.safe_input("请输入用户名: ")
            >>> if name:
            ...     print(f"你好, {name}")
        """
        if flush_before:
            self.flush_keyboard_buffer()
        try:
            result = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print("\n已取消")
            return None

        if not result:
            if not allow_empty:
                return default
            return ""

        return result

    def show_header(self, title: str, subtitle: Optional[str] = None) -> None:
        """
        显示标题头

        Args:
            title: 主标题
            subtitle: 副标题（可选）

        Example:
            >>> ui = UIHelper()
            >>> ui.show_header("主菜单", "v7.0.0")
        """
        print(self.HEADER_SEPARATOR)
        print(f"{title:^{self.UI_WIDTH}}")
        if subtitle:
            print(f"{subtitle:^{self.UI_WIDTH}}")
        print(self.HEADER_SEPARATOR)
        print()

    def confirm_action(
        self,
        prompt: str = "按回车键继续，或输入 N 取消",
        *,
        explicit: bool = False,
        default: bool = False,
        logger: Optional["ILogger"] = None,
    ) -> bool:
        """
        通用确认方法

        在 headless 模式下：
        - explicit=True 时自动拒绝（安全考虑）
        - explicit=False 时自动确认

        Args:
            prompt: 确认提示
            explicit: 是否需要显式确认（输入 Y/N）
            default: 默认值（headless 模式下使用）
            logger: 日志记录器（可选）

        Returns:
            用户是否确认

        Example:
            >>> ui = UIHelper()
            >>> if ui.confirm_action("确认删除所有数据?", explicit=True):
            ...     print("已删除")
        """
        if self.headless_mode:
            if explicit:
                if logger:
                    logger.warning(f"[Headless] 自动拒绝危险操作: {prompt}")
                print("Headless 模式下禁止自动确认危险操作，请使用交互模式执行")
                return False
            return default

        self.flush_keyboard_buffer()
        confirm = input(f"\n{prompt}: ").strip().upper()

        if explicit:
            if confirm == "Y":
                return True
            else:
                if confirm and confirm != "N":
                    print("无效输入，请输入 Y 确认或 N 取消")
                else:
                    print("已取消")
                return False
        else:
            return confirm != "N"

    def show_list_warning(self, list_id: str, show_advanced_hint: bool = False) -> None:
        """
        统一显示列表下载警告信息

        Args:
            list_id: 列表 ID
            show_advanced_hint: 是否显示高级参数提示
        """
        print(f"正在下载列表 ID: {list_id}")
        print("大型列表可能需要很长时间！")
        print("按 Ctrl+C 可安全暂停，稍后使用 [R] 恢复\n")

        if show_advanced_hint:
            print("当前版本暂不支持以下高级参数（预留接口）：")
            print("  - 跳过失败成员")
            print("  - 强制重新下载")
            if not self.headless_mode:
                input("按回车键开始下载...")

    # ==================== 新增消息打印方法 ====================

    def print_success(self, msg: str) -> None:
        """
        打印成功消息

        Args:
            msg: 消息内容
        """
        print(f" {msg}")

    def print_error(self, msg: str) -> None:
        """
        打印错误消息

        Args:
            msg: 消息内容
        """
        print(f" {msg}")

    def print_warning(self, msg: str) -> None:
        """
        打印警告消息

        Args:
            msg: 消息内容
        """
        print(f" {msg}")

    def print_info(self, msg: str) -> None:
        """
        打印信息消息

        Args:
            msg: 消息内容
        """
        print(f" {msg}")

    def print_menu_option(self, key: str, label: str, desc: str) -> None:
        """打印菜单选项（统一格式）

        Args:
            key: 选项键
            label: 选项标签
            desc: 选项描述
        """
        label_width = display_width(label)
        padding = 12 - label_width + len(label)  # 调整填充以补偿中文字符

        if desc:
            print(f"  [{key}] {label:<{padding}} → {desc}")
        else:
            print(f"  [{key}] {label}")

    def print_status_line(self, label: str, value: str, status: str = "") -> None:
        """打印状态行（统一格式）

        Args:
            label: 标签名
            value: 值
            status: 状态文本
        """
        label_width = display_width(label)
        padding = 10 - label_width + len(label)  # 调整填充以补偿中文字符

        status_str = f" [{status}]" if status else ""
        print(f"  {label:<{padding}} {value}{status_str}")

    def print_separator(self) -> None:
        """
        打印标准分隔线
        """
        print(self.SEPARATOR_LINE)

    # ==================== 新增输入方法 ====================

    def input_number(
        self,
        prompt: str,
        *,
        min_val: Optional[int] = None,
        max_val: Optional[int] = None,
        default: Optional[int] = None,
    ) -> Optional[int]:
        """
        输入数字

        支持范围验证和默认值。

        Args:
            prompt: 输入提示
            min_val: 最小值（可选）
            max_val: 最大值（可选）
            default: 默认值（空输入时使用）

        Returns:
            用户输入的数字，如果无效则返回 None

        Example:
            >>> ui = UIHelper()
            >>> count = ui.input_number("请输入数量 (1-10): ", min_val=1, max_val=10)
            >>> if count:
            ...     print(f"选择了 {count} 个")
        """
        self.flush_keyboard_buffer()
        try:
            result = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print("\n已取消")
            return None

        # 空输入处理
        if not result:
            if default is not None:
                return default
            return None

        # 数字验证
        try:
            value = int(result)
        except ValueError:
            print("无效输入，请输入整数")
            return None

        # 范围验证
        if min_val is not None and value < min_val:
            print(f"输入值不能小于 {min_val}")
            return None
        if max_val is not None and value > max_val:
            print(f"输入值不能大于 {max_val}")
            return None

        return value

    def confirm_yes_no(
        self,
        prompt: str,
        *,
        default: bool = False,
    ) -> bool:
        """
        是/否确认

        要求用户输入 Y 或 N 进行确认。

        Args:
            prompt: 确认提示
            default: 默认值（空输入时使用）

        Returns:
            用户是否确认

        Example:
            >>> ui = UIHelper()
            >>> if ui.confirm_yes_no("是否继续?"):
            ...     print("继续执行")
        """
        default_hint = "[Y/n]" if default else "[y/N]"
        self.flush_keyboard_buffer()
        try:
            result = input(f"{prompt} {default_hint}: ").strip().upper()
        except (EOFError, KeyboardInterrupt):
            print("\n已取消")
            return False

        if not result:
            return default

        if result in ("Y", "YES"):
            return True
        elif result in ("N", "NO"):
            return False
        else:
            print("无效输入，请输入 Y 或 N")
            return default

    # ==================== 延迟方法 ====================

    def delay(
        self,
        seconds: int = 0,
        *,
        min_seconds: int = 0,
        max_seconds: int = 0,
        message: str = "",
        show_countdown: bool = True,
        allow_skip: bool = False,
        countdown_template: str = "      等待中: {i:2d} 秒（按回车继续）",
    ) -> bool:
        """
        统一的延迟方法

        支持固定秒数或随机秒数延迟，可选显示倒计时和中断支持。
        在 headless 模式下自动降级为静默等待。

        Args:
            seconds: 固定延迟秒数（与 min_seconds/max_seconds 二选一）
            min_seconds: 随机延迟最小秒数（需与 max_seconds 配合使用）
            max_seconds: 随机延迟最大秒数（<=0 或 min > max 则使用固定秒数）
            message: 延迟开始前显示的消息（可选）
            show_countdown: 是否显示倒计时（False 则只显示消息后静默等待）
            allow_skip: 是否允许回车跳过等待
            countdown_template: 倒计时显示模板，{i} 会被替换为剩余秒数

        Returns:
            True 表示正常结束，False 表示被用户中断或跳过

        Example:
            # 固定延迟，可中断
            >>> ui.delay(seconds=2, message="2秒后继续...", allow_skip=True)

            # 随机延迟（防风控）
            >>> ui.delay(min_seconds=5, max_seconds=10, message="防风控延迟...", allow_skip=True)

            # 简单静默延迟
            >>> ui.delay(seconds=1)

            # 倒计时显示
            >>> ui.delay(seconds=8, message="自动关闭...", show_countdown=True)
        """
        if max_seconds > 0 and min_seconds <= max_seconds:
            delay_sec = random.randint(min_seconds, max_seconds)
        else:
            delay_sec = seconds

        if delay_sec <= 0:
            return True

        if self.headless_mode:
            time.sleep(delay_sec)
            return True

        if message:
            print(message)

        if show_countdown and allow_skip:
            self.flush_keyboard_buffer()
            print()
            for i in range(delay_sec, 0, -1):
                print(f"\r{countdown_template.format(i=i)}", end="", flush=True)
                for _ in range(int(1 / C.COUNTDOWN_INTERVAL)):
                    if msvcrt is not None and msvcrt.kbhit():
                        key = msvcrt.getch()
                        if key in (b"\r", b"\n"):
                            while msvcrt.kbhit():
                                msvcrt.getch()
                            print()
                            return False
                    time.sleep(C.COUNTDOWN_INTERVAL)
            print()
            return True
        elif show_countdown:
            for i in range(delay_sec, 0, -1):
                print(f"\r{countdown_template.format(i=i)}", end="", flush=True)
                time.sleep(1)
            print()
            return True
        else:
            time.sleep(delay_sec)
            return True

    # ==================== 静态方法 ====================

    def flush_keyboard_buffer(self) -> None:
        """
        清空 Windows 键盘缓冲区

        清除所有待处理的键盘输入，防止残留输入影响后续操作。
        仅在 Windows 平台有效，其他平台静默跳过。
        """
        if msvcrt is not None:
            while msvcrt.kbhit():
                msvcrt.getch()

__all__ = ["UIHelper"]
