# -*- coding: utf-8 -*-
"""
路径迁移菜单模块

提供路径迁移功能的菜单界面。

主要功能：
- 全局路径替换
- 用户路径修改
- 列表路径修改
"""

from __future__ import annotations

# 标准库
import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional, Tuple

if TYPE_CHECKING:
    from ..services.database_service import DatabaseService
    from ..tmd_types import IConfig, IDatabaseService, ILogger, IUIHelper

# 第三方库（无）

# 本地模块
from ..utils.path_utils import normalize_path
from .base_menu import BaseMenu


class PathMenu(BaseMenu):
    """
    路径迁移菜单

    提供路径迁移功能的菜单界面。

    Attributes:
        ui: UI 辅助实例
        logger: 日志实例
        config: 配置实例
        database_service: 数据库服务实例

    Example:
        >>> from tmdc.menus.path_menu import PathMenu
        >>> menu = PathMenu(ui, logger, config, database_service)
        >>> menu.show()
    """

    def __init__(
        self,
        ui: "IUIHelper",
        logger: "ILogger",
        config: "IConfig",
        database_service: "IDatabaseService",
    ) -> None:
        """
        初始化路径迁移菜单

         Args:
             ui: UI 辅助实例
             logger: 日志实例
             config: 配置实例
             database_service: 数据库服务实例
        """
        super().__init__(ui, logger, config)
        self.database_service = database_service

    # ==================== 公共接口 ====================

    def show(self) -> None:
        """
        显示路径迁移菜单
        """
        while True:
            self.ui.clear_screen()
            self.ui.show_header("迁移路径")

            # 显示数据库路径统计
            stats = self._get_path_statistics()

            if stats:
                user_count, user_dir_count, list_count, list_dir_count = stats
                print(f"  用户实体:   {user_count} 个，涉及 {user_dir_count} 个不同路径")
                print(f"  列表实体:   {list_count} 个，涉及 {list_dir_count} 个不同路径")
            else:
                print("  用户实体:   [无法读取] ❌")
                print("  列表实体:   [无法读取] ❌")

            # 显示当前配置的路径
            if self.config.root_path:
                expanded = str(Path(self.config.root_path).expanduser())
                exists = "✅" if Path(expanded).exists() else "⚠️  (不存在)"
                print(f"  当前配置:   {expanded} {exists}")
            else:
                print("  当前配置:   [未配置] ❌")
            print()

            self.ui.print_separator()

            # 操作选项
            print("  [1] 全局替换路径    → 批量替换所有路径前缀（移动文件夹后使用）")
            print("  [2] 修改特定用户    → 搜索并修改单个用户的路径")
            print("  [3] 修改特定列表    → 搜索并修改单个列表的路径")
            print("  [0] 返回配置向导\n")
            print("💡 提示: 修改前建议先备份 foo.db 文件，避免误操作")

            self.ui.flush_keyboard_buffer()
            choice = input("请选择 [0-3]: ").strip().upper()

            if choice == "0":
                break
            elif choice == "1":
                self._migrate_global_path()
            elif choice == "2":
                self._migrate_entity_path("user")
            elif choice == "3":
                self._migrate_entity_path("list")
            else:
                continue

    # ==================== 私有方法 ====================

    def _get_path_statistics(self) -> Optional[Tuple[int, int, int, int]]:
        """
        获取数据库中的路径统计信息

        Returns:
            元组 (user_count, user_dir_count, list_count, list_dir_count)，
            如果查询失败则返回 None
        """
        with self.database_service.db_session() as cursor:
            if cursor is None:
                return None

            try:
                # 统计用户实体路径
                cursor.execute("SELECT COUNT(DISTINCT parent_dir) FROM user_entities")
                user_dir_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM user_entities")
                user_count = cursor.fetchone()[0]

                # 统计列表实体路径
                cursor.execute("SELECT COUNT(DISTINCT parent_dir) FROM lst_entities")
                list_dir_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM lst_entities")
                list_count = cursor.fetchone()[0]

                return (user_count, user_dir_count, list_count, list_dir_count)

            except sqlite3.Error as e:
                self.logger.error(f"统计路径失败: {e}")
                return None

    def _migrate_global_path(self) -> None:
        """
        全局路径替换

        批量替换数据库中所有路径的指定前缀。
        """
        self.ui.clear_screen()
        self.ui.show_header("全局路径替换")

        print("功能: 批量替换数据库中所有路径的指定前缀")
        print("示例: 将 'D:/OldPath' 替换为 'E:/NewPath'\n")

        old_path = self.ui.safe_input("  旧路径前缀: ", allow_empty=True)
        if not old_path:
            print("\n📝 已取消")
            self.ui.pause()
            return

        new_path = self.ui.safe_input("  新路径前缀: ", allow_empty=True)
        if not new_path:
            print("\n📝 已取消")
            self.ui.pause()
            return

        # 标准化路径分隔符（统一使用 Windows 反斜杠，与 TMD Go 保持一致）
        old_path = normalize_path(old_path)
        new_path = normalize_path(new_path)

        # 预览将要修改的记录
        with self.database_service.db_session() as cursor:
            if cursor is None:
                self.ui.pause()
                return

            try:
                # 查找匹配的用户实体
                cursor.execute(
                    """
                    SELECT ue.id, u.screen_name, ue.parent_dir
                    FROM user_entities ue
                    JOIN users u ON ue.user_id = u.id
                    WHERE ue.parent_dir LIKE ?
                """,
                    (old_path + "%",),
                )
                user_matches = cursor.fetchall()

                # 查找匹配的列表实体
                cursor.execute(
                    """
                    SELECT le.id, l.name, le.parent_dir
                    FROM lst_entities le
                    JOIN lsts l ON le.lst_id = l.id
                    WHERE le.parent_dir LIKE ?
                """,
                    (old_path + "%",),
                )
                list_matches = cursor.fetchall()
            except sqlite3.Error as e:
                print(f"\n❌ 查询失败: {e}")
                self.ui.pause()
                return

        total_matches = len(user_matches) + len(list_matches)

        if total_matches == 0:
            print(f"\n⚠️  未找到以 '{old_path}' 开头的路径")
            self.ui.pause()
            return

        print(f"\n找到 {len(user_matches)} 个用户实体和 {len(list_matches)} 个列表实体")

        # 显示部分预览
        if user_matches:
            print("\n用户实体预览（前5个）:")
            for row in user_matches[:5]:
                new_dir = row["parent_dir"].replace(old_path, new_path)
                print(f"  @{row['screen_name']}: {new_dir}")
            if len(user_matches) > 5:
                print(f"  ... 还有 {len(user_matches) - 5} 个")

        if list_matches:
            print("\n列表实体预览（前5个）:")
            for row in list_matches[:5]:
                new_dir = row["parent_dir"].replace(old_path, new_path)
                print(f"  {row['name']}: {new_dir}")
            if len(list_matches) > 5:
                print(f"  ... 还有 {len(list_matches) - 5} 个")

        self.ui.print_separator()

        # 确认操作
        confirm = input(f"确认替换 {total_matches} 条记录? [Y/N]: ").strip().upper()
        if confirm != "Y":
            print("📝 已取消")
            self.ui.pause()
            return

        # 执行替换
        operations = [
            (
                """UPDATE user_entities SET parent_dir = REPLACE(parent_dir, ?, ?) WHERE parent_dir LIKE ?""",
                (old_path, new_path, old_path + "%"),
            ),
            (
                """UPDATE lst_entities SET parent_dir = REPLACE(parent_dir, ?, ?) WHERE parent_dir LIKE ?""",
                (old_path, new_path, old_path + "%"),
            ),
        ]

        try:
            self.database_service.execute_transaction(operations)
            print("\n✅ 路径替换完成:")
            print(f"  用户实体: {len(user_matches)} 条记录已更新")
            print(f"  列表实体: {len(list_matches)} 条记录已更新")
            self.logger.info(
                f"路径迁移: '{old_path}' -> '{new_path}' (用户:{len(user_matches)}, 列表:{len(list_matches)})"
            )
        except sqlite3.Error as e:
            print(f"\n❌ 路径替换失败: {e}")

        self.ui.pause()

    def _migrate_entity_path(self, entity_type: str) -> None:
        """
        通用实体路径迁移方法

        Args:
            entity_type: 实体类型 ('user' 或 'list')
        """
        is_user = entity_type == "user"
        title = "修改用户路径" if is_user else "修改列表路径"
        label = "用户" if is_user else "列表"

        self.ui.clear_screen()
        self.ui.show_header(title)

        if is_user:
            keyword = self.ui.safe_input(f"  {label}名关键词: ", allow_empty=True)
            if not keyword:
                print("\n📝 已取消")
                self.ui.pause()
                return
        else:
            list_id = self.ui.safe_input(f"  {label} ID: ", allow_empty=True)
            if not list_id or not list_id.isdigit():
                if list_id:
                    print("\n❌ 无效的列表 ID")
                    self.ui.pause()
                return

        # 查询实体
        with self.database_service.db_session() as cursor:
            if cursor is None:
                self.ui.pause()
                return

            try:
                if is_user:
                    cursor.execute(
                        """
                        SELECT ue.id, ue.user_id, u.screen_name, u.name, ue.parent_dir, ue.name as entity_name
                        FROM user_entities ue
                        JOIN users u ON ue.user_id = u.id
                        WHERE u.screen_name LIKE ? OR u.name LIKE ?
                    """,
                        (f"%{keyword}%", f"%{keyword}%"),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT le.id, le.lst_id, l.name, le.parent_dir, le.name as entity_name
                        FROM lst_entities le
                        JOIN lsts l ON le.lst_id = l.id
                        WHERE le.lst_id = ?
                    """,
                        (list_id,),
                    )

                entities = cursor.fetchall()
            except sqlite3.Error as e:
                print(f"\n❌ 查询失败: {e}")
                self.ui.pause()
                return

        if not entities:
            search_key = keyword if is_user else list_id
            print(f"\n📝 未找到匹配 '{search_key}' 的{label}")
            self.ui.pause()
            return

        print(f"\n找到 {len(entities)} 个{label}实体:")
        for i, entity in enumerate(entities[:10], 1):
            if is_user:
                print(f"  [{i}] @{entity['screen_name']} ({entity['name']})")
            else:
                print(f"  [{i}] {entity['name']} - {entity['entity_name']}")
            print(f"      当前路径: {entity['parent_dir']}")

        if len(entities) > 10:
            print(f"  ... 还有 {len(entities) - 10} 个")

        if len(entities) == 1:
            entity = entities[0]
        else:
            choice = self.ui.safe_input("\n选择序号 (或回车取消): ", allow_empty=True)
            if not choice or not choice.isdigit():
                print("\n📝 已取消")
                self.ui.pause()
                return

            idx = int(choice) - 1
            if not (0 <= idx < len(entities)):
                print("\n❌ 无效的序号")
                self.ui.pause()
                return
            entity = entities[idx]

        display_name = (
            f"@{entity['screen_name']}"
            if is_user
            else f"{entity['name']} - {entity['entity_name']}"
        )
        print(f"\n已选择: {display_name}")
        print(f"当前路径: {entity['parent_dir']}")

        new_path = self.ui.safe_input("\n  新路径: ", allow_empty=True)
        if not new_path:
            print("\n📝 已取消")
            self.ui.pause()
            return

        # 标准化路径
        new_path = normalize_path(new_path)

        self.ui.print_separator()

        # 确认
        confirm = input("确认修改? [Y/N]: ").strip().upper()
        if confirm != "Y":
            print("📝 已取消")
            self.ui.pause()
            return

        # 执行更新
        table = "user_entities" if is_user else "lst_entities"
        operations = [(f"UPDATE {table} SET parent_dir = ? WHERE id = ?", (new_path, entity["id"]))]

        try:
            self.database_service.execute_transaction(operations)
            print("\n✅ 路径已更新:")
            print(f"  {label}: {display_name}")
            print(f"  新路径: {new_path}")
            self.logger.info(f"{label}路径修改: {display_name} -> {new_path}")
        except sqlite3.Error as e:
            print(f"\n❌ 路径修改失败: {e}")

        self.ui.pause()


__all__ = ["PathMenu"]
