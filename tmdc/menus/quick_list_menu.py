# -*- coding: utf-8 -*-
"""
固定列表菜单模块

提供固定列表管理功能，包括添加、删除、排序和下载列表。

主要功能：
- 固定列表管理菜单
- 添加/删除列表
- 列表排序（调整下载顺序）
- 选择并下载列表
"""

from __future__ import annotations

# 标准库
import copy
from typing import TYPE_CHECKING, List, Optional, Tuple

if TYPE_CHECKING:
    from ..tmd_types import IConfig, IDatabaseService, IDownloadService, ILogger, IUIHelper

# 第三方库（无）

# 本地模块
from .base_menu import BaseMenu


class QuickListMenu(BaseMenu):
    """
    固定列表菜单

    提供固定列表管理功能，管理常用列表 ID 配置。

    Attributes:
        ui: UI 辅助实例
        logger: 日志实例
        config: 配置实例
        download_service: 下载服务实例
        database_service: 数据库服务实例

    Example:
        >>> from tmdc.menus.quick_list_menu import QuickListMenu
        >>> menu = QuickListMenu(ui, logger, config, download_service, database_service)
        >>> menu.show()
    """

    # ==================== 初始化 ====================

    def __init__(
        self,
        ui: "IUIHelper",
        logger: "ILogger",
        config: "IConfig",
        download_service: "IDownloadService",
        database_service: "IDatabaseService",
    ) -> None:
        """
        初始化固定列表菜单

        Args:
            ui: UI 辅助实例
            logger: 日志实例
            config: 配置实例
            download_service: 下载服务实例
            database_service: 数据库服务实例
        """
        super().__init__(ui, logger, config)
        self.download_service = download_service
        self.database_service = database_service

    # ==================== 公共接口 ====================

    def show(self) -> None:
        """
        显示固定列表管理菜单
        """
        while True:
            self.ui.clear_screen()
            self.ui.show_header("固定列表管理")

            # 状态显示
            self._display_quick_list_status()

            self.ui.print_separator()

            # 操作选项
            self.ui.print_menu_option("1", "添加列表", "添加新的列表ID")
            self.ui.print_menu_option("2", "删除列表", "移除列表")
            self.ui.print_menu_option("3", "排序列表", "调整列表下载顺序（上移/下移）")
            self.ui.print_menu_option("4", "立即下载", "选择列表开始下载")
            self.ui.print_menu_option("0", "返回上级菜单", "")
            print("提示: [Q] 键将按当前顺序下载所有列表")

            choice = self.ui.safe_input("\n请选择 [0-4]: ", allow_empty=True)
            if choice is None:
                continue
            choice = choice.upper()

            if choice == "0":
                break
            elif choice == "1":
                self._add_quick_list()
            elif choice == "2":
                self._remove_quick_list()
            elif choice == "3":
                self._sort_quick_lists()
            elif choice == "4":
                self._select_and_download_quick_list()
            else:
                continue

    def download_all_quick_lists(self) -> None:
        """
        顺序下载所有固定列表

        此方法供主菜单 [Q] 键调用。
        """
        if not self.config.quick_list_ids:
            print("\n尚未配置固定列表！")
            self.ui.pause()
            return

        list_count = len(self.config.quick_list_ids)
        interval = self.config.quick_list_interval  # 读取配置

        self.ui.clear_screen()
        self.ui.show_header("顺序下载所有固定列表")

        print(f"将按顺序下载 {list_count} 个固定列表")
        print(f"列表间将自动间隔 {interval} 秒，防止触发限流\n")

        failed_lists: List[str] = []
        all_failed_users: List[str] = []

        for i, list_id in enumerate(self.config.quick_list_ids, 1):
            print(f"\n{'=' * 60}")
            print(f"[{i}/{list_count}] 正在下载: {list_id}")
            print("=" * 60)

            success, failed_users = self._download_quick_list(
                list_id,
                batch_mode=True,
                show_progress=(i, list_count),
            )

            if not success:
                failed_lists.append(list_id)
                print(f"\n列表 {list_id} 下载失败")

            if failed_users:
                all_failed_users.extend(failed_users)

            # 列表间间隔（最后一个列表不需要间隔）
            if i < list_count and interval > 0:
                self.ui.delay(seconds=interval, message=f"\n等待 {interval} 秒后继续下一个列表...", allow_skip=True)

        # 汇总报告
        self._print_batch_summary(list_count, failed_lists, all_failed_users)
        self.ui.pause()

    # ==================== 列表操作方法 ====================

    def _add_quick_list(self) -> None:
        """添加固定列表（事务性保存版）"""
        list_id = self.ui.safe_input("\n请输入列表ID (10位以上数字ID): ", allow_empty=True)

        if not list_id or not list_id.isdigit() or len(list_id) < 10:
            print("无效的列表ID，必须是10位以上纯数字")
            self.ui.pause()
            return

        if list_id in self.config.quick_list_ids:
            print(f"列表 {list_id} 已存在")
            self.ui.pause()
            return

        new_ids = copy.deepcopy(self.config.quick_list_ids)
        new_ids.append(list_id)

        success, error = self.config.save_quick_list_ids(new_ids)

        if success:
            print(f"已添加列表 {list_id}")
            print(f"当前共 {len(new_ids)} 个列表，[Q] 键将按顺序下载所有")
        else:
            print(f"添加失败: {error}")
            print("配置未更改，请检查文件权限")

        self.ui.pause()

    def _remove_quick_list(self) -> None:
        """删除固定列表（事务性保存版）"""
        if not self.config.quick_list_ids:
            print("没有可删除的列表")
            self.ui.pause()
            return

        print("\n当前固定列表:")
        for i, list_id in enumerate(self.config.quick_list_ids, 1):
            print(f"  [{i}] {list_id}")

        choice = self.ui.safe_input("\n请输入要删除的序号 (或回车取消): ", allow_empty=True)

        if not choice or not choice.isdigit():
            return

        idx = int(choice) - 1
        if 0 <= idx < len(self.config.quick_list_ids):
            removed = self.config.quick_list_ids[idx]

            # 确认删除
            if not self.ui.confirm_action(f"确认删除列表 {removed}?", explicit=True):
                print("📝 已取消")
                self.ui.pause()
                return

            new_ids = copy.deepcopy(self.config.quick_list_ids)
            new_ids.pop(idx)

            success, error = self.config.save_quick_list_ids(new_ids)

            if success:
                print(f"✅ 已删除列表 {removed}")
            else:
                print(f"❌ 删除失败: {error}")
                print("配置未更改")
        else:
            print("无效的序号")

        self.ui.pause()

    def _sort_quick_lists(self) -> None:
        """排序固定列表（事务性保存版）"""
        if len(self.config.quick_list_ids) < 2:
            print("需要至少2个列表才能排序")
            self.ui.pause()
            return

        print("\n当前列表顺序（[Q] 将按此顺序下载）:")
        for i, list_id in enumerate(self.config.quick_list_ids, 1):
            print(f"  [{i}] {list_id}")

        print("\n请输入要移动的列表序号")
        choice = self.ui.safe_input("选择列表 (或回车取消): ", allow_empty=True)

        if not choice or not choice.isdigit():
            return

        idx = int(choice) - 1
        if not (0 <= idx < len(self.config.quick_list_ids)):
            print("无效的序号")
            self.ui.pause()
            return

        list_id = self.config.quick_list_ids[idx]
        print(f"\n已选择: [{idx + 1}] {list_id}")
        print(f"请输入新位置 (1-{len(self.config.quick_list_ids)})")
        new_pos_input = self.ui.safe_input(f"移动到位置 (当前为 {idx + 1}): ", allow_empty=True)

        if not new_pos_input or not new_pos_input.isdigit():
            print("无效的位置")
            self.ui.pause()
            return

        new_pos = int(new_pos_input) - 1
        if not (0 <= new_pos < len(self.config.quick_list_ids)):
            print("位置超出范围")
            self.ui.pause()
            return

        if new_pos == idx:
            print("位置未改变")
            self.ui.pause()
            return

        new_ids = copy.deepcopy(self.config.quick_list_ids)
        new_ids.pop(idx)
        new_ids.insert(new_pos, list_id)

        success, error = self.config.save_quick_list_ids(new_ids)

        if success:
            direction = "前移" if new_pos < idx else "后移"
            print(f"已将列表 {list_id} {direction}到第 {new_pos + 1} 位")
            self.logger.info(f"列表排序: {list_id} 从 {idx + 1} 移动到 {new_pos + 1}")
        else:
            print(f"保存排序失败: {error}")
            print("已恢复原顺序")

        self.ui.pause()

    def _select_and_download_quick_list(self) -> None:
        """选择并下载固定列表"""
        if not self.config.quick_list_ids:
            print("未配置固定列表")
            self.ui.pause()
            return

        if len(self.config.quick_list_ids) == 1:
            selected = self.config.quick_list_ids[0]
        else:
            print("\n选择要下载的列表:")
            for i, list_id in enumerate(self.config.quick_list_ids, 1):
                print(f"  [{i}] {list_id}")

            choice = self.ui.safe_input(
                f"\n请选择 [1-{len(self.config.quick_list_ids)}]: ", allow_empty=True
            )
            if not choice or not choice.isdigit():
                return
            idx = int(choice) - 1
            if 0 <= idx < len(self.config.quick_list_ids):
                selected = self.config.quick_list_ids[idx]
            else:
                print("无效选择")
                self.ui.pause()
                return

        success, failed_users = self._download_quick_list(selected)

        if failed_users:
            print(f"\n共有 {len(failed_users)} 个用户下载失败:")
            for user in failed_users[:5]:
                print(f"  - {user}")
            if len(failed_users) > 5:
                print(f"  ... 还有 {len(failed_users) - 5} 个")
            print("\n可使用 [R] 恢复下载 重试失败的用户")

        self.ui.pause()

    def _download_quick_list(
        self,
        list_id: str,
        *,
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
            Tuple[bool, List[str]]: (是否成功, 失败用户列表)
        """
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

    # ==================== 辅助方法 ====================

    def _display_quick_list_status(self) -> None:
        """显示固定列表状态"""
        if not self.config.quick_list_ids:
            self.ui.print_status_line("当前状态", "[未配置任何固定列表]")
            print("  提示: 添加后可在主菜单按 [Q] 顺序下载所有列表\n")
        else:
            self.ui.print_status_line("列表数量", f"共 {len(self.config.quick_list_ids)} 个")
            print()
            print("  当前固定列表:")
            print("  序号   列表ID                   下载顺序")
            print("  ----   --------------------     --------")
            for i, list_id in enumerate(self.config.quick_list_ids, 1):
                print(f"  {i:<4}   {list_id:<20}     第{i}个")
            print()

    def _print_batch_summary(
        self,
        total_count: int,
        failed_lists: List[str],
        failed_users: List[str],
    ) -> None:
        """
        打印批量下载汇总报告

        Args:
            total_count: 总列表数
            failed_lists: 失败的列表 ID 列表
            failed_users: 失败的用户列表
        """
        print("\n" + "=" * 60)
        print("批量下载完成")
        print("=" * 60)

        success_count = total_count - len(failed_lists)
        print(f"成功: {success_count}/{total_count} 个列表")

        if failed_lists:
            print(f"\n失败的列表 ({len(failed_lists)} 个):")
            for list_id in failed_lists:
                print(f"  - {list_id}")

        if failed_users:
            print(f"\n失败的用户 ({len(failed_users)} 个):")
            for user in failed_users[:10]:
                print(f"  - {user}")
            if len(failed_users) > 10:
                print(f"  ... 还有 {len(failed_users) - 10} 个")
            print("\n可使用 [R] 恢复下载 重试失败的用户")


__all__ = ["QuickListMenu"]
