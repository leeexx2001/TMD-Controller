# -*- coding: utf-8 -*-
"""
时间戳菜单模块

提供时间戳管理功能的简化菜单界面
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    import logging

    from ..services.database_service import DatabaseService
    from ..services.timestamp_service import TimestampService
    from ..tmd_types import IConfig, IUIHelper

from ..parsers import DateParser
from .base_menu import BaseMenu


class TimestampMenu(BaseMenu):
    """时间戳菜单

    提供时间戳管理功能的简化菜单界面

    Attributes:
        database_service: 数据库服务实例
        timestamp_service: 时间戳服务实例
    """

    def __init__(
        self,
        ui: "IUIHelper",
        logger: "logging.Logger",
        config: "IConfig",
        database_service: "DatabaseService",
        timestamp_service: "TimestampService",
    ) -> None:
        """初始化时间戳菜单

        Args:
            ui: UI 辅助工具实例
            logger: 日志实例
            config: 配置实例
            database_service: 数据库服务实例
            timestamp_service: 时间戳服务实例
        """
        super().__init__(ui, logger, config)
        self.database_service = database_service
        self.timestamp_service = timestamp_service

    def show(self) -> None:
        """显示时间戳管理菜单"""
        if not self.database_service.is_database_available():
            print(self.database_service.get_database_unavailable_message())
            self.ui.pause()
            return

        self.ui.clear_screen()
        self.ui.show_header("时间戳管理")

        print("搜索用户或列表，设置同步时间戳\n")
        print("💡 输入用户名关键词或列表ID，如: wudi 或 123456789")
        print("💡 时间格式: 2024-01-15 | 7d(7天前) | yesterday | today\n")

        while True:
            keyword = self.ui.safe_input("搜索 (0返回): ", allow_empty=True)
            if not keyword:
                continue
            if keyword == "0":
                break

            keyword = keyword.strip()
            if not keyword:
                continue

            targets = self.database_service.find_targets(keyword)
            if not targets:
                self._handle_new_target(keyword)
                continue

            self._show_targets_and_manage(targets)

    def _show_targets_and_manage(self, targets: List[Dict[str, Any]]) -> None:
        """显示搜索结果并管理

        Args:
            targets: 搜索结果列表
        """
        print(f"\n找到 {len(targets)} 个结果:")
        for i, t in enumerate(targets[:10], 1):
            ts_display = self.timestamp_service.format_timestamp_display(
                t.get("timestamp"), default_empty="未设置"
            )
            if t["type"] == "user":
                name = t.get("name") or ""
                print(f"  {i}. @{t['screen_name']} ({name}) - {ts_display}")
            else:
                print(f"  {i}. 📋 列表 {t['id']} - {ts_display}")

        if len(targets) > 10:
            print(f"  ... 还有 {len(targets) - 10} 个")

        choice = self.ui.safe_input("\n选择序号 (回车取消): ", allow_empty=True)
        if not choice or not choice.isdigit():
            return

        idx = int(choice) - 1
        if not (0 <= idx < len(targets)):
            print("❌ 无效序号")
            self.ui.pause()
            return

        self._manage_target(targets[idx])

    def _manage_target(self, target: Dict[str, Any]) -> None:
        """管理单个目标的时间戳

        Args:
            target: 目标信息字典
        """
        target_type = target.get("type", "user")
        ts_display = self.timestamp_service.format_timestamp_display(
            target.get("timestamp"), default_empty="未设置(全量下载)"
        )

        if target_type == "user":
            screen_name = target.get("screen_name", "unknown")
            header = f"@{screen_name}"
        else:
            header = f"列表 {target.get('id', '?')}"

        print(f"\n📋 {header}  当前: {ts_display}")

        time_input = self.ui.safe_input("新时间 (回车=重置全量下载, 0=取消): ", allow_empty=True)

        if time_input == "0":
            return

        target_date = None
        if time_input and time_input.strip():
            target_date = DateParser.parse(time_input.strip())
            if target_date is None:
                print("❌ 时间格式无效")
                self.ui.pause()
                return

        self._apply_timestamp(target, target_date)

    def _apply_timestamp(self, target: Dict[str, Any], target_date: Optional[datetime]) -> None:
        """应用时间戳设置

        Args:
            target: 目标信息字典
            target_date: 目标日期，None 表示重置为全量下载
        """
        target_type = target.get("type", "user")

        if target_type == "user":
            screen_name = target.get("screen_name", "unknown")
            entity_id = target.get("entity_id")
            if entity_id:
                result = self.timestamp_service.set_sync_timestamp(entity_id, target_date)
            else:
                result = self.timestamp_service.get_or_create_user_entity(screen_name, target_date)
            self._show_result(result)
        else:
            list_id = target.get("id")
            if list_id:
                result = self.timestamp_service.batch_set_list_timestamp(list_id, target_date)
                self._show_batch_result(result)

        self.ui.pause()

    def _show_result(self, result: Any) -> None:
        """显示操作结果

        Args:
            result: 操作结果对象
        """
        if result.success:
            print(f"✅ {result.message}")
        else:
            print(f"❌ {result.error or result.message}")

    def _show_batch_result(self, result: Any) -> None:
        """显示批量操作结果

        Args:
            result: 批量操作结果对象
        """
        if result.success:
            print(f"✅ {result.message}")
            if result.failed_items:
                print(f"⚠️  失败项目: {', '.join(result.failed_items[:5])}")
                if len(result.failed_items) > 5:
                    print(f"   ... 还有 {len(result.failed_items) - 5} 个")
        else:
            print(f"❌ {result.error or result.message}")

    def _handle_new_target(self, keyword: str) -> None:
        """处理新目标创建

        Args:
            keyword: 用户输入的关键词
        """
        keyword = keyword.strip()
        if not keyword:
            return

        if keyword.isdigit():
            self._create_new_list(int(keyword))
        else:
            screen_name = keyword.lstrip("@")
            self._create_new_user(screen_name)

    def _create_new_user(self, screen_name: str) -> None:
        """创建新用户

        Args:
            screen_name: 用户名
        """
        if not screen_name:
            return

        print(f"\n📝 用户 @{screen_name} 不在数据库中")
        create = self.ui.safe_input("创建并设置时间戳? [Y/N]: ", allow_empty=True)
        if not create or create.upper() != "Y":
            return

        time_input = self.ui.safe_input("时间 (回车=全量下载): ", allow_empty=True)

        target_date = None
        if time_input and time_input.strip():
            target_date = DateParser.parse(time_input.strip())
            if target_date is None:
                print("❌ 时间格式无效")
                self.ui.pause()
                return

        result = self.timestamp_service.get_or_create_user_entity(screen_name, target_date)
        self._show_result(result)
        self.ui.pause()

    def _create_new_list(self, list_id: int) -> None:
        """创建新列表

        Args:
            list_id: 列表 ID
        """
        if list_id <= 0:
            print("❌ 无效的列表ID")
            return

        print(f"\n📝 列表 {list_id} 不在数据库中")
        create = self.ui.safe_input("创建并设置时间戳? [Y/N]: ", allow_empty=True)
        if not create or create.upper() != "Y":
            return

        time_input = self.ui.safe_input("时间 (回车=全量下载): ", allow_empty=True)

        target_date = None
        if time_input and time_input.strip():
            target_date = DateParser.parse(time_input.strip())
            if target_date is None:
                print("❌ 时间格式无效")
                self.ui.pause()
                return

        result = self.timestamp_service.get_or_create_list_entity(list_id, target_date)
        self._show_result(result)
        self.ui.pause()


__all__ = ["TimestampMenu"]
