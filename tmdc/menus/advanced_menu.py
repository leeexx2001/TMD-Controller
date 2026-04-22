#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""高级下载菜单模块"""

from __future__ import annotations

# 标准库
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional, Tuple

# 本地模块
from ..parsers.input_parser import InputParser
from ..utils.validators.username import clean_username
from .base_menu import BaseMenu

# 第三方库（无）


if TYPE_CHECKING:
    import logging

    from ..services.timestamp_service import TimestampService
    from ..tmd_types import IConfig, IDatabaseService, IDownloadService, IUIHelper
    from .resume_menu import ResumeMenu
    from .timestamp_menu import TimestampMenu


class AdvancedMenu(BaseMenu):
    """高级下载选项菜单

    提供多种高级下载模式的入口：
    - 单个输入精确控制
    - 批量输入
    - 文件导入
    - 关注下载
    - 组合模式
    - 禁用重试模式
    """

    def __init__(
        self,
        ui: "IUIHelper",
        logger: "logging.Logger",
        config: "IConfig",
        download_service: "IDownloadService",
        database_service: "IDatabaseService",
        resume_menu: Optional["ResumeMenu"] = None,
        timestamp_menu: Optional["TimestampMenu"] = None,
        timestamp_service: Optional["TimestampService"] = None,
    ) -> None:
        """初始化高级菜单

        Args:
            ui: UI服务实例
            logger: 日志器实例
            config: 配置实例
            download_service: 下载服务实例
            database_service: 数据库服务实例
            resume_menu: 恢复菜单实例
            timestamp_menu: 时间戳菜单实例
            timestamp_service: 时间戳服务实例
        """
        super().__init__(ui, logger, config)
        self.download_service = download_service
        self.database_service = database_service
        self.resume_menu = resume_menu
        self.timestamp_menu = timestamp_menu
        self.timestamp_service = timestamp_service

    # ==================== 公共接口 ====================

    def show(self) -> None:
        """显示高级下载菜单"""
        options = [
            ("1", "单个输入", "精确控制单个用户/列表参数"),
            ("2", "批量输入", "多用户名/列表ID混合"),
            ("3", "文件导入", "从文本文件读取任务列表（支持双轨风控延迟）"),
            ("4", "关注下载", "下载某账号的全部关注对象"),
            ("5", "组合模式", "自定义混合任务（用户+列表+关注）"),
            ("6", "禁用重试", "单用户下载（失败不自动重试）"),
            ("7", "自动关注", "向私密账号发送关注请求"),
            ("8", "重置全量", "重置时间戳后全量下载\n"),
            ("L", "孤立用户", "列出未关联列表的用户"),
            ("D", "删除项目", "从数据库中彻底删除某用户的所有数据"),
            ("T", "时间戳管理", "设置/重置同步时间戳，控制下载范围"),
            ("R", "恢复下载", "续传未完成任务"),
            ("0", "返回主菜单", ""),
        ]

        handlers = {
            "1": self._advanced_single_input,
            "2": self._advanced_batch_input,
            "3": self.menu_file_batch,
            "4": self.menu_following,
            "5": self.menu_combo,
            "6": self._advanced_no_retry_mode,
            "7": self._menu_auto_follow,
            "8": self._menu_reset_time_download,
            "L": self._menu_unlinked_users,
            "D": self._menu_delete_user_project,
            "T": self._menu_soft_reset,
            "R": self._menu_resume,
        }

        self._run_menu_loop(
            title="高级下载选项（按输入源分类）",
            options=options,
            handlers=handlers,
            hints=["双轨风控延迟配置在 [C]→[5] 中设置（区分成功/失败）"],
        )

    # ==================== 菜单处理方法 ====================

    def _advanced_single_input(self) -> None:
        """单个输入的精确控制"""
        self.ui.clear_screen()
        self.ui.show_header("单个输入 - 精确控制")

        print("支持格式：@username、twitter.com/user、列表URL、列表ID、Name(username)\n")

        from ..parsers.input_parser import InputParser

        user_input = self.ui.safe_input("回车退出或输入: ", allow_empty=True)
        if not user_input:
            return

        input_type, value, _ = InputParser.parse(user_input)

        if input_type == "unknown":
            print(f"\n❌ 无法识别输入格式: {user_input}")
            self.ui.pause()
            return

        print("\n💡 当前版本暂不支持以下高级参数（预留接口）：")
        print("  - 限制下载数量 (--limit)")
        print("  - 排除转推 (--no-retweet)")
        print("  - 强制重新下载 (--force)\n")

        if input_type == "numeric_id":
            from ..utils.validators.timestamp import handle_numeric_id_ambiguity

            input_type, value = handle_numeric_id_ambiguity(value, self.ui, mode="both")

        if input_type == "user":
            print(f"\n📥 开始下载用户: @{value}")
            result = self.download_service.download_user(value)
        elif input_type == "list":
            print(f"\n📥 开始下载列表: {value}")
            result = self.download_service.download_list(value)
        else:
            print(f"❌ 不支持的类型: {input_type}")
            self.ui.pause()
            return

        if result.success:
            print(result.get_success_message())
        else:
            print(result.get_error_message())
            if result.warn_users:
                print(f"⚠️ 警告用户: {', '.join(result.warn_users[:5])}")
            if result.error_messages:
                print(f"❌ 错误: {result.error_messages[0][:80]}")

        self.ui.pause()

    def _advanced_batch_input(self) -> None:
        """批量输入 - 命令行风格"""
        self.ui.clear_screen()
        self.ui.show_header("批量输入模式")

        if not self._check_config_or_return():
            return

        print("输入多个项目，用空格或逗号分隔")
        print("示例: user1, @user2, https://x.com/user3, Name(user4)")
        print("提示: 纯数字ID在批量模式下默认作为用户处理\n")

        user_input = self.ui.safe_input("回车退出或批量输入: ", allow_empty=True)
        if not user_input:
            return

        from ..parsers.input_parser import InputParser

        parsed = InputParser.parse_batch(user_input)
        if not parsed:
            print("❌ 无法解析输入")
            self.ui.pause()
            return

        users = [v for t, v in parsed if t == "user"]
        lists = [v for t, v in parsed if t == "list"]

        print(f"\n📥 开始批量下载 {len(users)} 个用户, {len(lists)} 个列表")
        print("-" * 62)

        result = self.download_service.download_batch(users=users, lists=lists)

        print(f"\n{result.get_success_message() if result.success else result.get_error_message()}")

        if result.warn_users:
            print(f"⚠️ 警告用户 ({len(result.warn_users)} 个): {', '.join(result.warn_users[:5])}")

        self.ui.pause()

    def _advanced_no_retry_mode(self) -> None:
        """禁用重试模式 - 单用户下载"""
        self.ui.clear_screen()
        self.ui.show_header("禁用重试模式")

        from ..parsers.input_parser import InputParser

        user_input = self.ui.safe_input("回车退出或输入用户名或URL: ", allow_empty=True)
        if not user_input:
            return

        input_type, value, _ = InputParser.parse(user_input)

        if input_type == "numeric_id":
            from ..utils.validators.timestamp import handle_numeric_id_ambiguity

            input_type, value = handle_numeric_id_ambiguity(value, self.ui, mode="user_only")
            if not input_type:
                return

        if input_type != "user" or not value:
            print(f"\n❌ 无法识别有效的用户名: '{value}'")
            self.ui.pause()
            return

        print(f"\n📝 识别：目标用户: @{value}")

        print("\n💡 此模式特点：")
        print("  ✓ 使用 --no-retry 参数")
        print("  ✓ 下载失败的推文不会自动重试")
        print("  ✓ 适合快速扫描近期推文，可能遗漏历史失败项")
        print("  ⚠️ 注意：仍会下载媒体文件！并非仅转储元数据\n")

        exit_code, _, _ = self.download_service.run_tmd(args=["--user", f"@{value}", "--no-retry"])

        if exit_code == 0:
            print("✅ 下载完成！")
        else:
            print("❌ 下载失败")
            print("📝 可随时恢复 - 已下载的文件是安全的")

        self.ui.pause()

    def _menu_reset_time_download(self) -> None:
        """重置时间戳后全量下载模式"""
        self.ui.clear_screen()
        self.ui.show_header("重置时间戳后全量下载")

        print("支持格式: URL、@用户名、列表ID、Name(username)")
        print("提示: 每行输入一个目标，空回车开始下载，输入0退出\n")
        print("⚠️ 此模式会先重置时间戳为全量下载，然后执行下载")
        print("⚠️ 适用于需要重新下载所有历史媒体的情况\n")

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

                from ..parsers.input_parser import InputParser

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

            print(f"\n📝 将处理 {len(users)} 个用户, {len(lists)} 个列表")
            print("-" * 62)

            failed_reset_users: List[str] = []
            failed_reset_lists: List[str] = []

            print("\n🔄 第一步: 重置时间戳（智能选择：数据库优先，特殊情况调用TMD）...")

            for user in users:
                print(f"  重置 @{user}...", end=" ")
                result = self.timestamp_service.get_or_create_user_entity(user, None)
                if result.success:
                    print("✅")
                else:
                    print(f"❌ ({result.error})")
                    failed_reset_users.append(user)

            for list_id in lists:
                print(f"  重置列表 {list_id}...", end=" ")
                result = self.timestamp_service.get_or_create_list_entity(int(list_id), None)
                if result.success:
                    print("✅")
                else:
                    print(f"❌ ({result.error})")
                    failed_reset_lists.append(list_id)

            if failed_reset_users or failed_reset_lists:
                print(f"\n⚠️ {len(failed_reset_users) + len(failed_reset_lists)} 个目标重置失败")
                if failed_reset_users:
                    print(f"   用户: {', '.join(failed_reset_users[:5])}")
                if failed_reset_lists:
                    print(f"   列表: {', '.join(failed_reset_lists[:5])}")

            print("\n📥 第二步: 开始全量下载...")
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

    def _menu_unlinked_users(self) -> None:
        """列出未关联列表的用户"""
        self.ui.clear_screen()
        self.ui.show_header("孤立用户 - 未关联列表")

        if not self.database_service.is_database_available():
            print(self.database_service.get_database_unavailable_message())
            self.ui.pause()
            return

        print("📋 查询存在于数据库但未关联任何列表的用户...\n")

        users = self.database_service.find_unlinked_users()

        if not users:
            print("✅ 没有找到孤立用户，所有用户都已关联列表。")
            self.ui.pause()
            return

        self.logger.info(f"查询孤立用户: 找到 {len(users)} 个未关联用户")

        # 按 is_accessible 字段分组
        accessible_users = [u for u in users if u.get("is_accessible")]
        inaccessible_users = [u for u in users if not u.get("is_accessible")]

        total = len(users)
        accessible_count = len(accessible_users)
        inaccessible_count = len(inaccessible_users)

        print(f"找到 {total} 个孤立用户（可访问: {accessible_count}, 不可访问: {inaccessible_count}）：\n")

        # 显示可访问账号表
        if accessible_users:
            print("=" * 71)
            print(f"✅ 可访问账号 ({accessible_count} 个)")
            print("=" * 71)
            print(f"{'序号':<6}{'用户名':<35}{'显示名称':<30}")
            print("-" * 71)

            for idx, user in enumerate(accessible_users, 1):
                screen_name = user.get("screen_name", "N/A")
                name = user.get("name", "N/A") or "N/A"
                user_url = f"https://x.com/{screen_name}"
                print(f"{idx:<6}{user_url:<35}{name:<30}")

            print()

        # 显示不可访问账号表
        if inaccessible_users:
            print("=" * 71)
            print(f"❌ 不可访问账号 ({inaccessible_count} 个)")
            print("=" * 71)
            print(f"{'序号':<6}{'用户名':<35}{'显示名称':<30}")
            print("-" * 71)

            for idx, user in enumerate(inaccessible_users, 1):
                screen_name = user.get("screen_name", "N/A")
                name = user.get("name", "N/A") or "N/A"
                user_url = f"https://x.com/{screen_name}"
                print(f"{idx:<6}{user_url:<35}{name:<30}")

            print()

        print("=" * 71)
        print(f"\n💡 这些用户存在于数据库中，但未关联任何列表。")
        print(f"   ✅ 可访问: {accessible_count} 个 | ❌ 不可访问: {inaccessible_count} 个")

        # 遍历功能选项
        print("\n" + "-" * 71)
        print("遍历选项:")
        if accessible_users:
            print("  [1] 遍历可访问账号 (执行 tmd --user 更新 is_accessible)")
        if inaccessible_users:
            print("  [2] 遍历不可访问账号 (执行 tmd --user 更新 is_accessible)")
        print("  [0] 返回")
        print("-" * 71)

        while True:
            choice = self.ui.safe_input("\n选择 [1/2/0]: ", allow_empty=True)
            if choice is None:
                continue
            choice = choice.strip()

            if choice == "0" or choice == "":
                return
            elif choice == "1" and accessible_users:
                self._traverse_users(accessible_users, "可访问")
                break
            elif choice == "2" and inaccessible_users:
                self._traverse_users(inaccessible_users, "不可访问")
                break
            else:
                print("❌ 无效选择，请重新输入")

    def _traverse_users(self, users: List[Dict[str, Any]], user_type: str) -> None:
        """遍历用户列表并执行 tmd --user 命令

        Args:
            users: 用户列表
            user_type: 用户类型描述（用于显示）
        """
        total = len(users)
        print(f"\n🔄 开始遍历 {user_type} 账号，共 {total} 个用户")
        print("=" * 71)

        for idx, user in enumerate(users, 1):
            screen_name = user.get("screen_name", "N/A")
            name = user.get("name", "N/A") or "N/A"

            print(f"\n[{idx}/{total}] 正在处理: @{screen_name} ({name})")
            print("-" * 71)

            # 执行 tmd --user 命令
            exit_code, stdout, stderr = self.download_service.run_tmd(
                args=["--user", f"@{screen_name}"],
                capture_output=True
            )

            if exit_code == 0:
                print(f"✅ @{screen_name} 处理完成")
            else:
                print(f"❌ @{screen_name} 处理失败")
                if stderr:
                    print(f"   错误: {stderr[:200]}")

            # 显示进度
            if idx < total:
                print(f"\n📊 进度: {idx}/{total} ({idx * 100 // total}%)")

        print("\n" + "=" * 71)
        print(f"✅ 遍历完成！共处理 {total} 个 {user_type} 账号")
        print("💡 每个用户的 is_accessible 字段已通过 tmd --user 更新")
        self.ui.pause()

    def _menu_delete_user_project(self) -> None:
        """从数据库中删除用户项目的所有数据"""
        self.ui.clear_screen()
        self.ui.show_header("删除用户项目")

        if not self.database_service.is_database_available():
            print(self.database_service.get_database_unavailable_message())
            self.ui.pause()
            return

        print("⚠️ 危险操作：此操作将从数据库中彻底删除指定用户的全部数据！")
        print("   包括：用户信息、下载实体、历史名称、列表关联\n")
        print("支持格式: @用户名、用户名、数字ID\n")

        user_input = self.ui.safe_input("回车退出或输入目标: ", allow_empty=True)
        if not user_input:
            return

        input_type, value, _ = InputParser.parse(user_input)

        if input_type == "numeric_id":
            uid = int(value)
            screen_name = f"(ID:{uid})"
        elif input_type == "user":
            screen_name = value
            users = self.database_service.find_users(value, limit=5)
            if not users:
                print(f"\n❌ 未找到用户: @{value}")
                self.ui.pause()
                return
            if len(users) > 1:
                print(f"\n找到 {len(users)} 个匹配用户:")
                for i, u in enumerate(users, 1):
                    print(f"  [{i}] @{u['screen_name']} ({u['name']})")
                idx = self.ui.input_number(
                    "请选择序号: ", min_val=1, max_val=len(users)
                )
                if idx is None:
                    print("📝 已取消")
                    self.ui.pause()
                    return
                selected = users[idx - 1]
            else:
                selected = users[0]
            uid = selected["id"]
            screen_name = selected["screen_name"]
        else:
            print(f"\n❌ 无法识别输入: {user_input}")
            self.ui.pause()
            return

        user_info = self.database_service.get_user_entity_info(screen_name) if input_type == "user" else None
        entity_count = 0
        if user_info and user_info.get("entity_id"):
            entity_count = 1

        print(f"\n📋 即将删除:")
        print(f"   用户: @{screen_name} (ID: {uid})")
        if entity_count:
            print(f"   下载实体: {entity_count} 个")
        print()

        if not self.ui.confirm_action(f"确认删除 @{screen_name} 的所有数据? [y/N]", explicit=True):
            print("📝 已取消删除操作")
            self.ui.pause()
            return

        print(f"\n🗑️ 正在删除 @{screen_name} 的所有数据...")
        success, message, stats = self.database_service.delete_user_project(uid)

        if success:
            print(f"\n✅ {message}")
            print(f"   关联链接: {stats['links']} 条")
            print(f"   下载实体: {stats['entities']} 条")
            print(f"   历史名称: {stats['names']} 条")
            print(f"   用户记录: {stats['users']} 条")
            self.logger.info(
                f"删除用户项目: @{screen_name}(uid={uid}), "
                f"links={stats['links']}, entities={stats['entities']}, "
                f"names={stats['names']}, users={stats['users']}"
            )
        else:
            print(f"\n❌ {message}")

        self.ui.pause()

    def _menu_resume(self) -> None:
        """调用恢复下载菜单"""
        if self.resume_menu:
            self.resume_menu.show()

    def _menu_soft_reset(self) -> None:
        """调用时间戳管理菜单"""
        if self.timestamp_menu:
            self.timestamp_menu.show()

    def _menu_auto_follow(self) -> None:
        """自动关注模式（私密账号专用）"""
        self.ui.clear_screen()
        self.ui.show_header("自动关注模式（私密账号专用）")

        from ..parsers.input_parser import InputParser

        user_input = self.ui.safe_input("回车退出或输入私密账号用户名或URL: ", allow_empty=True)
        if not user_input:
            return

        input_type, username, _ = InputParser.parse(user_input)

        if input_type == "numeric_id":
            from ..utils.validators.timestamp import handle_numeric_id_ambiguity

            input_type, username = handle_numeric_id_ambiguity(username, self.ui, mode="user_only")
            if not input_type:
                return

        if input_type != "user":
            print("\n❌ 自动关注仅支持用户ID")
            self.ui.pause()
            return

        print(f"\n📝 正在为 {username} 发送关注请求...")
        print("📝 发送成功后，你必须等待对方批准才能下载！")

        exit_code, _, _ = self.download_service.run_tmd(args=["--auto-follow", "--user", f"@{username}"])

        if exit_code == 0:
            print("✅ 关注请求已发送！")
            print("💡 一旦对方批准，使用主菜单快捷输入即可下载。")
        else:
            print("❌ 关注请求失败")

        self.ui.pause()

    # ==================== 功能方法 ====================

    def menu_file_batch(self) -> None:
        """文件批量导入（双轨延迟版）"""

        def _logic():
            print("请准备文本文件，每行一个用户名/URL（仅支持用户）")
            print("支持格式: 用户名、@用户名、twitter.com/username、Name(username)")
            print("💡 列表下载请使用 [Q] 快速下载 或 --auto-q CLI模式")
            print(f"💡 当前分批大小为 {self.config.file_batch_size} 行/批")

            if self.config.is_batch_delay_success_enabled:
                print(
                    f"      成功延迟: {self.config.batch_delay_success_min}-{self.config.batch_delay_success_max}秒（防服务器压力）"
                )
            if self.config.is_batch_delay_fail_enabled:
                print(
                    f"      失败延迟: {self.config.batch_delay_fail_min}-{self.config.batch_delay_fail_max}秒（防风控）"
                )

            print("      可在 [C]→[4] 中调整这些设置\n")

            filepath = self.ui.safe_input("回车退出或输入文件路径: ", allow_empty=True)
            if filepath:
                filepath = filepath.strip("\"'")
            if not filepath:
                return

            path = Path(filepath)

            if not path.exists():
                print(f"\n❌ 文件不存在: {path}")
                return

            # 读取并解析文件
            result = self._read_and_parse_file(path)
            if result is None:
                return
            lines, users, lists = result

            print(f"📝 解析结果: {len(users)} 个用户, {len(lists)} 个列表")

            # 用户确认
            if not self.ui.confirm_action("确认执行? [Y/n]", explicit=False):
                return

            # 使用分批处理机制
            self._process_file_batch(path, lines)

        self.ui.clear_screen()
        self.ui.show_header("文件批量导入")
        if not self._check_config_or_return():
            return
        _logic()
        self.ui.pause()

    def _process_file_batch(
        self,
        file_path: Path,
        lines: List[str],
    ) -> None:
        """统一文件批处理核心（双轨延迟版）

        Args:
            file_path: 文件路径
            lines: 文件内容行列表
        """
        batch_size = self.config.file_batch_size
        total = len(lines)

        print(f"📝 文件模式：读取: {file_path.name}（共 {total} 行，分批大小: {batch_size}）")

        delay_status = []
        if self.config.is_batch_delay_success_enabled:
            delay_status.append(
                f"成功:{self.config.batch_delay_success_min}-{self.config.batch_delay_success_max}s"
            )
        if self.config.is_batch_delay_fail_enabled:
            delay_status.append(
                f"失败:{self.config.batch_delay_fail_min}-{self.config.batch_delay_fail_max}s"
            )

        if delay_status:
            print(f"💡 风控延迟: {', '.join(delay_status)}")
        else:
            print("💡 风控延迟: 禁用（可在 [C]→[4] 中配置）")

        if total > batch_size * 3:
            print(f"💡 任务较多（>{batch_size * 3}行），已启用分批防卡顿保护")
        print("💡 按 Ctrl+C 可随时安全暂停，已下载内容不会丢失\n")

        batch_num = 0
        processed = 0
        failed_batches = []
        all_failed_items = []

        try:
            for i in range(0, total, batch_size):
                batch = lines[i : i + batch_size]
                batch_num += 1
                processed += len(batch)

                print()
                self.ui.print_separator()
                print(f"批次 {batch_num}")
                self.ui.print_separator()

                # 显示全部任务
                print(f"任务: {', '.join(batch)}")

                # 解析批次内容
                all_parsed = []
                for line in batch:
                    parsed = InputParser.parse_batch(line)
                    all_parsed.extend(parsed)

                users = [v for t, v in all_parsed if t == "user"]
                lists = [v for t, v in all_parsed if t == "list"]

                # 批量下载
                result = self.download_service.download_batch(users=users, lists=lists)

                # 处理结果
                if result.warn_users:
                    all_failed_items.extend(result.warn_users)
                    batch_success = False
                else:
                    batch_success = result.success

                if batch_success:
                    print(
                        f"✅ 批次 {batch_num} 完成，进度 {processed}/{total} ({processed * 100 // total}%)"
                    )
                    if processed < total and self.config.is_batch_delay_success_enabled:
                        self._apply_batch_delay(
                            self.config.batch_delay_success_min,
                            self.config.batch_delay_success_max,
                            "本批次下载成功，执行防压力延迟...",
                        )
                else:
                    failed_batches.append(batch_num)
                    print(
                        f"⚠️ 第 {batch_num} 批存在失败任务，进度 {processed}/{total} ({processed * 100 // total}%)"
                    )

                    if processed < total and self.config.is_batch_delay_fail_enabled:
                        self._apply_batch_delay(
                            self.config.batch_delay_fail_min,
                            self.config.batch_delay_fail_max,
                            "⚠️ 本批次下载失败，执行风控延迟...",
                        )
                    elif processed < total:
                        self.ui.delay(seconds=1, message="⏳ 继续下一批...", show_countdown=False)

            print()
            self.ui.print_separator()
            if not failed_batches:
                status = "全部成功"
            elif all_failed_items:
                status = f"部分完成（失败: {len(all_failed_items)}个）"
            else:
                status = f"部分完成（失败批次: {failed_batches}）"
            print(f"✅ 文件处理完成！共 {batch_num} 批，{processed} 行 - {status}")

            if all_failed_items:
                print(f"\n⚠️ 失败项目列表 ({len(all_failed_items)}个):")
                print("   " + " ".join(all_failed_items[:20]))
                if len(all_failed_items) > 20:
                    print(f"   ... 还有 {len(all_failed_items) - 20} 个")

            self.ui.print_separator()

            self.logger.info(
                f"文件批量下载完成: {file_path.name}, "
                f"共{batch_num}批{processed}行, 失败{len(failed_batches)}批, "
                f"失败项目{len(all_failed_items)}个"
            )

        except KeyboardInterrupt:
            print(f"\n\n🛑 用户手动停止，已完成 {processed}/{total} 行")
            self.logger.info(f"分批下载被中断于第{batch_num}批")

    def _apply_batch_delay(self, min_sec: int, max_sec: int, message: str) -> None:
        """应用批次延迟

        Args:
            min_sec: 最小延迟秒数
            max_sec: 最大延迟秒数
            message: 延迟提示消息
        """
        self.ui.delay(min_seconds=min_sec, max_seconds=max_sec, message=message, allow_skip=True)

    def _read_and_parse_file(
        self, file_path: Path
    ) -> Optional[Tuple[List[str], List[str], List[str]]]:
        """读取并解析文件，返回 (lines, users, lists)

        Args:
            file_path: 文件路径

        Returns:
            (lines, users, lists) 元组，失败返回 None
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"\n❌ 读取文件失败: {e}")
            return None

        if not lines:
            print("\n❌ 文件为空")
            return None

        all_parsed = []
        for line in lines:
            parsed = InputParser.parse_batch(line)
            all_parsed.extend(parsed)

        if not all_parsed:
            print("\n❌ 未能解析任何有效输入")
            return None

        users = [v for t, v in all_parsed if t == "user"]
        lists = [v for t, v in all_parsed if t == "list"]

        return lines, users, lists

    def menu_following(self) -> None:
        """关注列表下载"""

        def _logic():
            print("下载指定账号关注的所有用户的媒体。")
            print("⚠️ 警告：如果目标关注人数较多（>1000），这可能需要数小时！\n")

            target = self.ui.safe_input("回车退出或输入准确目标用户名: ", allow_empty=True)
            if not target:
                return

            target = clean_username(target)
            if not target:
                print("\n❌ 无效的用户名")
                return
            print(f"\n⚠️ 你即将下载 {target} 关注的所有用户！")
            print("⚠️ 根据关注数量，这可能需要很长时间！")

            if not self.ui.confirm_action("确认下载关注列表? [y/N]", explicit=True):
                print("📝 已取消")
                return

            print(f"\n📝 开始下载 {target} 的关注列表...")
            exit_code, _, _ = self.download_service.run_tmd(args=["--foll", f"@{target}"])
            if exit_code == 0:
                print("✅ 关注列表下载完成！")
            else:
                print("❌ 关注列表下载失败")
                print("📝 可随时恢复 - 已下载的文件是安全的")

        self.ui.clear_screen()
        self.ui.show_header("关注列表下载")
        if not self._check_config_or_return():
            return
        _logic()
        self.ui.pause()

    def menu_combo(self) -> None:
        """组合下载模式"""
        self.ui.clear_screen()
        self.ui.show_header("组合下载模式")

        if not self._check_config_or_return():
            return

        print("在一个任务中组合多种下载方式。")
        print("支持直接粘贴URL，系统自动识别类型")
        print("不需要的选项请直接留空。\n")

        users_input = self.ui.safe_input(
            "回车退出或输入\n用户列表（空格/逗号分隔）: ", allow_empty=True
        )
        if users_input is None:
            return

        lists_input = self.ui.safe_input("列表ID/URL（空格/逗号分隔）: ", allow_empty=True)
        if lists_input is None:
            return

        follows_input = self.ui.safe_input("关注列表目标（空格分隔）: ", allow_empty=True)
        if follows_input is None:
            return

        users, lists, follows = [], [], []

        if users_input:
            parsed = InputParser.parse_batch(users_input)
            users = [v for t, v in parsed if t == "user"]
            lists.extend([v for t, v in parsed if t == "list"])

        if lists_input:
            parsed = InputParser.parse_batch(lists_input)
            lists.extend([v for t, v in parsed if t == "list"])
            users.extend([v for t, v in parsed if t == "user"])

        if follows_input:
            follows = [cleaned for u in follows_input.split() if (cleaned := clean_username(u))]

        users = list(dict.fromkeys(users))
        lists = list(dict.fromkeys(lists))

        if not users and not lists and not follows:
            print("📝 没有选择任何任务。")
            self.ui.pause()
            return

        print("\n📝 识别结果：")
        len(users) + len(lists)
        self.ui.print_status_line("用户", f"{len(users)} 个")
        self.ui.print_status_line("列表", f"{len(lists)} 个")
        if follows:
            self.ui.print_status_line("关注", ', '.join(follows[:3]) + ("..." if len(follows) > 3 else ""))

        success, _ = self._execute_combo(users, lists, follows)
        if not success:
            print("📝 部分任务未完成")
        self.ui.pause()

    def _execute_combo(
        self, users: List[str], lists: List[str], follows: List[str]
    ) -> Tuple[bool, List[str]]:
        """执行组合下载，返回 (成功与否, 失败项目列表)

        Args:
            users: 用户名列表
            lists: 列表ID列表
            follows: 关注目标列表

        Returns:
            Tuple[bool, List[str]]: (是否成功, 失败项目列表)
        """
        args = []
        for user in users:
            args.extend(["--user", f"@{user}"])
        for lst in lists:
            args.extend(["--list", lst])
        for f in follows:
            args.extend(["--foll", f"@{f}"])

        if not args:
            print("📝 没有选择任何任务。")
            return False, []

        print(f"\n📝 组合任务: {len(users)}用户/{len(lists)}列表/{len(follows)}关注")
        self.ui.safe_input("按回车键开始执行...", allow_empty=True)

        print("\n📝 开始组合下载...")
        exit_code, _, _ = self.download_service.run_tmd(args=args)

        if exit_code == 0:
            print("✅ 组合任务完成！")
            return True, []
        else:
            print("❌ 组合任务失败")
            print("📝 可随时恢复 - 已下载的文件是安全的")
            return False, users + lists

    # ==================== 辅助方法 ====================

    def _check_list_exists(self, list_id: str) -> bool:
        """检查列表是否已存在于数据库中

        Args:
            list_id: 列表ID（字符串格式）

        Returns:
            bool: 列表存在返回 True，否则返回 False
        """
        try:
            list_id_int = int(list_id)
        except ValueError:
            return False
        return self.database_service.check_list_metadata_exists(list_id_int)


__all__ = ["AdvancedMenu"]
