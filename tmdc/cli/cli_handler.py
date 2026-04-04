# -*- coding: utf-8 -*-
"""
CLI 处理器模块

从原始文件 TMD_Controller_v6.7.2.py 第 1057-1550 行迁移。
提供命令行参数解析和处理功能。

主要功能：
- argparse 参数解析
- 维护模式处理
- 时间戳设置 CLI 命令
"""

from __future__ import annotations

# 标准库
import argparse
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Dict, Optional, Tuple

if TYPE_CHECKING:
    from ..container import Container
    from ..services.database_service import DatabaseService
    from ..services.timestamp_service import TimestampService

# 第三方库（无）

# 本地模块
from ..constants import C, VERSION
from ..parsers import DateParser
from ..parsers.input_parser import InputParser
from ..tmd_types import BatchOperationResult, OperationResult
from ..utils import clean_username, get_errors_json_path, parse_timestamp_target


class CLIHandler:
    """
    CLI 自动化处理类

    提供命令行参数解析和处理功能，支持维护模式和时间戳管理。

    Attributes:
        container: 依赖注入容器
        config: 配置实例
        logger: 日志实例

    Example:
        >>> from tmdc.container import Container
        >>> container = Container.get_instance()
        >>> handler = CLIHandler(container)
        >>> parser = handler.create_parser()
        >>> args = parser.parse_args(['-u', 'elonmusk'])
    """

    def __init__(self, container: "Container") -> None:
        """
        初始化 CLI 处理器

        Args:
            container: 依赖注入容器
        """
        self.container = container
        self.config = container.config
        self.logger = container.logger
        self.database_service = container.database_service
        self._download_service = None

    @property
    def download_service(self):
        """获取下载服务实例（延迟加载）"""
        if self._download_service is None:
            self._download_service = self.container.resolve("download_service")
        return self._download_service

    def create_parser(self) -> argparse.ArgumentParser:
        """
        创建参数解析器

        Returns:
            argparse.ArgumentParser: 配置好的参数解析器

        Note:
            v4.12.0 集成时间戳管理
        """
        parser = argparse.ArgumentParser(
            description=f"Twitter Media Downloader Controller v{VERSION} - Windows专用版",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
                使用示例:
                  %(prog)s                           # 启动交互式菜单（默认）
                  %(prog)s -u elonmusk               # 直接下载用户
                  %(prog)s -l 1234567890 -H          # 无头模式下载列表
                  %(prog)s -r                         # 恢复未完成下载（交互模式：每轮询问选择）
                  %(prog)s -r -H                      # 恢复未完成下载（无头模式：自动持续运行直到完成）
                  %(prog)s --file users.txt          # 批量导入（自动分批，风控延迟）
                  %(prog)s --combo "user1,list:123"  # 组合任务（自动过滤空值）
                  %(prog)s --auto-q                  # 自动按顺序下载所有配置的固定列表

                恢复下载说明:
                  - 仅 -r: 交互模式，每轮结束后显示菜单:
                    [1] 自动循环模式后补救下载（默认）
                    [2] 继续下一轮
                    [0] 退出
                  - -r -H: 完全自动模式，无需任何交互，持续运行直到所有任务完成
                  - 自动循环结束后会自动执行补救下载（绕开TMD），处理顽固失败任务

                时间戳管理示例:
                  %(prog)s --ts-set "user:elonmusk,7d"           # 只下载最近7天的内容
                  %(prog)s --ts-set "list:123456,2024-01-15"     # 列表从1月15日开始
                  %(prog)s --ts-reset "user:elonmusk"            # 重置为全量下载
                  %(prog)s --ts-reset "@elonmusk"                # 简写形式（重置用户）
                  %(prog)s --ts-set "user:elonmusk,30d" --ts-dry-run  # 预览变更

                时间格式说明:
                  绝对时间: 2024-01-15 | 2024-01-15 08:30 | 01-15(自动补全年份)
                  相对时间: 7d(7天前) | 2w(2周前) | 1m(1月前) | 3h(3小时前) | yesterday | today | now

                Profile 下载示例:
                  %(prog)s --profile-user elonmusk  # 仅下载用户 Profile（头像、横幅、简介）
                  %(prog)s --profile-user elonmusk --profile-user NASA  # 下载多个用户
                  %(prog)s --profile-list 1234567890  # 下载列表成员的 Profile
                  %(prog)s --profile-list 111 --profile-list 222  # 下载多个列表成员

                注意事项:
                  - 时间戳设置后立即生效，下次下载将只获取该时间之后的推文
                  - 列表操作会影响列表内所有成员，请谨慎使用
                  - --ts-dry-run 可预览变更，避免误操作数据库
                  - 支持自动创建不存在的用户/列表，设置时自动询问
                  - Profile 下载仅下载用户资料，不下载推文媒体
                """,
        )

        parser.add_argument(
            "-v",
            "--version",
            action="version",
            version=f"%(prog)s v{VERSION}",
            help="显示版本号并退出",
        )

        target_group = parser.add_mutually_exclusive_group()
        target_group.add_argument(
            "-u", "--user", metavar="USERNAME", help="直接下载指定用户（支持URL、@前缀、括号格式）"
        )
        target_group.add_argument(
            "-l", "--list", metavar="LIST_ID", help="直接下载指定列表ID（10位以上数字）"
        )
        target_group.add_argument("-f", "--foll", metavar="USERNAME", help="下载指定账号的关注列表")
        target_group.add_argument(
            "--file",
            metavar="PATH",
            type=Path,
            help="从文本文件批量导入（每行一个用户名/URL，UTF-8编码，自动分批+防风控，仅支持用户）",
        )
        target_group.add_argument(
            "--combo", metavar="ITEMS", help="组合模式（逗号分隔，格式: user1,list:123,foll:user2）"
        )
        target_group.add_argument(
            "--auto-q",
            action="store_true",
            help="自动模式：按顺序下载所有配置的固定列表并自动维护（需先配置，未配置时报错）",
        )
        target_group.add_argument(
            "-r",
            "--resume",
            action="store_true",
            help="恢复未完成下载（支持智能循环，自动循环结束后执行补救下载）",
        )

        parser.add_argument(
            "-n", "--no-retry", action="store_true", help="禁用失败重试（--no-retry 模式）"
        )
        parser.add_argument(
            "-a", "--auto-follow", action="store_true", help="自动关注私密账号（--auto-follow）"
        )
        parser.add_argument("-d", "--dbg", action="store_true", help="调试模式（--dbg）")

        parser.add_argument(
            "-H",
            "--headless",
            action="store_true",
            help="无头模式：无交互提示、无暂停、危险操作自动拒绝（适合脚本自动化）",
        )
        parser.add_argument(
            "-c",
            "--config",
            metavar="PATH",
            type=Path,
            help="指定自定义配置文件路径（默认: %%APPDATA%%/.tmd2/conf.yaml）",
        )

        maint_group = parser.add_mutually_exclusive_group()
        maint_group.add_argument(
            "-S", "--stats", action="store_true", help="显示下载统计（失败/待处理任务数）后退出"
        )

        ts_group = parser.add_argument_group("时间戳管理（Timestamp Manager）")
        ts_group.add_argument(
            "--ts-set",
            metavar="TARGET,TIME",
            help="设置同步时间戳（增量下载），格式: user:username,7d 或 list:id,2024-01-15，支持自动创建新用户/列表",
        )
        ts_group.add_argument(
            "--ts-reset",
            metavar="TARGET",
            help="重置为初始状态（全量下载），格式: user:username 或 list:id 或 @username，支持自动创建新用户/列表",
        )
        ts_group.add_argument(
            "--ts-dry-run", action="store_true", help="仅预览变更，不实际写入数据库"
        )
        ts_group.add_argument(
            "--ts-force", action="store_true", help="跳过列表操作的警告提示（用于脚本自动化场景）"
        )

        profile_group = parser.add_argument_group("Profile 下载（仅下载用户资料，不下载推文）")
        profile_group.add_argument(
            "--profile-user",
            metavar="USERNAME",
            action="append",
            help="仅下载指定用户的 Profile（头像、横幅、简介等），可重复使用",
        )
        profile_group.add_argument(
            "--profile-list",
            metavar="LIST_ID",
            action="append",
            help="仅下载指定列表成员的 Profile，可重复使用",
        )

        return parser

    def run(self, argv: list) -> int:
        """
        CLI 主入口方法

        Args:
            argv: 命令行参数列表

        Returns:
            int: 退出码（0=成功，非0=失败，-1=需要启动交互模式）
        """
        parser = self.create_parser()
        args = parser.parse_args(argv)

        # 设置无头模式
        if args.headless:
            self._set_headless_mode(True)

        try:
            # 维护模式
            if args.stats:
                return self.handle_maintenance(args)

            # 时间戳管理
            if args.ts_set or args.ts_reset:
                return self.handle_timestamp(args)

            # 自动模式
            if args.auto_q:
                return self.handle_auto_mode(args)

            # 恢复下载
            if args.resume:
                return self.handle_resume_mode(args)

            # 文件批量模式
            if args.file:
                return self.handle_file_mode(args)

            # 组合模式
            if args.combo:
                return self.handle_combo_mode(args)

            # Profile 下载
            if args.profile_user or args.profile_list:
                return self.handle_profile_download(args)

            # 单目标下载
            if args.user or args.list or args.foll:
                return self.handle_single_download(args)

            # 无参数，返回 -1 表示需要启动交互模式
            return -1

        except KeyboardInterrupt:
            print("\n📝 操作被用户中断")
            return 130
        except Exception as e:
            self.logger.critical(f"CLI 运行时错误: {e}", exc_info=True)
            print(f"\n❌ 致命错误: {e}")
            return 1

    def handle_maintenance(self, args: argparse.Namespace) -> int:
        """
        处理维护模式

        Args:
            args: 解析后的命令行参数

        Returns:
            int: 退出码（0=成功，1=失败）
        """
        if args.stats:
            print("📝 正在检查失败/待处理任务...")
            try:
                self._show_stats()
                return 0
            except Exception as e:
                self.logger.error(f"显示统计失败: {e}")
                return 1

        return 0

    def _show_stats(self) -> None:
        """显示下载统计信息"""
        if not self._check_db_available():
            return

        try:
            with self.database_service.db_session() as cursor:
                if cursor is None:
                    print("❌ 无法连接数据库")
                    return

                # 用户实体统计
                cursor.execute("SELECT COUNT(*) FROM user_entities")
                user_count = cursor.fetchone()[0]

                # 列表实体统计
                cursor.execute("SELECT COUNT(*) FROM lst_entities")
                list_count = cursor.fetchone()[0]

                print(f"用户实体: {user_count} 个")
                print(f"列表实体: {list_count} 个")

                # 检查 errors.json
                errors_path = self._get_errors_path()
                if errors_path and errors_path.exists():
                    import json

                    with open(errors_path, "r", encoding="utf-8") as f:
                        errors_data = json.load(f)
                    pending_count = sum(len(tweets) for tweets in errors_data.values())
                    if pending_count > 0:
                        print(f"\n⚠️ 待处理失败推文: {pending_count} 个")
                        print("💡 使用恢复下载功能可续传未完成任务")
                    else:
                        print("\n✅ 没有待处理的失败任务")
                else:
                    print("\n✅ 没有待处理的失败任务")

        except Exception as e:
            print(f"❌ 获取统计失败: {e}")

    def _check_db_available(self) -> bool:
        """
        检查数据库是否可用（委托给 DatabaseService）

        Returns:
            数据库可用返回 True，否则返回 False
        """
        if not self.database_service.is_database_available():
            print(self.database_service.get_database_unavailable_message())
            return False
        return True

    def _get_errors_path(self) -> Optional[Path]:
        """获取 errors.json 路径（委托给 utils.file_io）"""
        return get_errors_json_path(self.config.root_path)

    def handle_timestamp(self, args: argparse.Namespace) -> int:
        """
        处理时间戳设置 CLI 命令

        独立于下载流程，仅操作数据库，不需要完整配置（仅需数据库可访问）。

        Args:
            args: 解析后的命令行参数

        Returns:
            int: 退出码（0=成功，1=失败）
        """
        if not self._check_db_available():
            return 1

        dry_run = args.ts_dry_run

        # 检查 --ts-set 和 --ts-reset 是否同时提供
        if args.ts_set and args.ts_reset:
            print("--ts-set 和 --ts-reset 不能同时使用")
            print("请只选择其中一个选项")
            return 1

        try:
            if args.ts_set:
                target, time_str = self._parse_ts_arg(args.ts_set)
                if not target:
                    return 1

                if not time_str:
                    print("--ts-set 需要指定时间，格式: target,time")
                    print("示例: user:elonmusk,7d")
                    return 1

                # 使用 DateParser 解析日期
                target_date = DateParser.parse(time_str)
                if target_date is None:
                    print(f"无效的时间格式: {time_str}")
                    print(
                        "支持格式: 2024-01-15 | 2024-01-15 08:30 | 7d | 2w | 1m | yesterday | today"
                    )
                    return 1

                return self._execute_timestamp_set(target, target_date, dry_run, args.ts_force)

            elif args.ts_reset:
                target, _ = self._parse_ts_arg(args.ts_reset)
                if not target:
                    return 1

                return self._execute_timestamp_set(target, None, dry_run, args.ts_force)
            else:
                print("请指定 --ts-set 或 --ts-reset")
                return 1

        except Exception as e:
            self.logger.warning(f"时间戳设置失败: {e}")
            print(f"操作失败: {e}")
            return 1

    def _parse_ts_arg(self, arg_str: str) -> Tuple[Optional[Dict[str, str]], Optional[str]]:
        """
        解析时间戳参数中的目标部分（委托给 utils.validators）

        Args:
            arg_str: 参数字符串，格式如 "user:elonmusk,7d" 或 "list:123"

        Returns:
            Tuple[Optional[Dict], Optional[str]]:
                (target_dict, time_part) 或 (None, None) 如果解析失败
                target_dict: {"type": "user"|"list", "id": str}

        Example:
            >>> handler._parse_ts_arg("user:elonmusk,7d")
            ({'type': 'user', 'id': 'elonmusk'}, '7d')
        """
        return parse_timestamp_target(arg_str)

    def _execute_timestamp_set(
        self,
        target: Dict[str, str],
        target_date: Optional[datetime],
        dry_run: bool,
        force: bool = False,
    ) -> int:
        """
        执行单个时间戳设置操作（支持自动创建新用户/列表）

        Args:
            target: {"type": "user"|"list", "id": str}
            target_date: None 表示重置（全量下载），否则为起始时间
            dry_run: 是否仅预览
            force: 是否跳过列表操作的警告提示

        Returns:
            int: 退出码（0=成功，1=失败）
        """
        # 使用容器中的服务和时间戳服务
        db_service = self.database_service
        ts_service = self.container.timestamp_service

        target_type = target["type"]
        target_id = target["id"]

        if target_date is None:
            time_desc = "初始状态（全量下载）"
        else:
            time_desc = target_date.strftime("%Y-%m-%d %H:%M:%S")
            now = datetime.now()
            diff = now - target_date
            if diff.days > 0:
                time_desc += f"（约 {diff.days} 天前）"
            elif diff.seconds >= 3600:
                time_desc += f"（约 {diff.seconds // 3600} 小时前）"

        if dry_run:
            print(f"[预览模式] 将设置 {target_type}:{target_id} 的时间戳为: {time_desc}")
            return 0

        if target_type == "user":
            return self._handle_user_timestamp(
                target_id, target_date, time_desc, db_service, ts_service
            )

        elif target_type == "list":
            return self._handle_list_timestamp(
                target_id, target_date, time_desc, force, db_service, ts_service
            )

        return 1

    def _print_timestamp_success(
        self, username: str, target_date: Optional[datetime], time_desc: str
    ) -> None:
        """
        打印时间戳设置成功消息

        Args:
            username: 用户名
            target_date: 目标时间戳
            time_desc: 时间描述
        """
        action = "重置" if target_date is None else "设置"
        print(f"已{action} @{username} 的同步时间戳")
        if target_date:
            print(f"   下次下载将只获取 {time_desc} 之后的内容")
        else:
            print("   下次下载将获取全部历史内容")

    def _handle_user_timestamp(
        self,
        target_id: str,
        target_date: Optional[datetime],
        time_desc: str,
        db_service: "DatabaseService",
        ts_service: "TimestampService",
    ) -> int:
        """处理用户时间戳设置（支持自动创建）"""
        users = db_service.find_users_for_reset(target_id)

        if not users:
            # 用户不存在，尝试自动创建
            print(f"用户 '{target_id}' 不在数据库中，尝试自动创建...")
            result = ts_service.get_or_create_user_entity(target_id, target_date)

            if result.success:
                screen_name = (
                    result.data.get("screen_name", target_id) if result.data else target_id
                )
                self._print_timestamp_success(screen_name, target_date, time_desc)
                return 0
            else:
                print(f"❌ {result.error}")
                print("可能原因：用户名不存在、网络问题或 TMD 配置错误")
                return 1

        if len(users) > 1:
            print(f"找到 {len(users)} 个匹配用户:")
            for i, u in enumerate(users[:5], 1):
                current_ts = u.get("latest_release_time", "从未同步")
                print(f"   {i}. @{u['screen_name']} ({u['name']}) - {current_ts}")
            if len(users) > 5:
                print(f"   ... 还有 {len(users) - 5} 个")
            print(f"\n将操作第一个匹配项: @{users[0]['screen_name']}")

        user = users[0]

        entity_id = user.get("entity_id")
        if entity_id is None:
            # 用户无实体，尝试创建
            print(f"用户 @{user['screen_name']} 暂无下载记录，正在创建实体...")
            result = ts_service.get_or_create_user_entity(user["screen_name"], target_date)
            if result.success:
                self._print_timestamp_success(user["screen_name"], target_date, time_desc)
                return 0
            else:
                print(f"❌ {result.error}")
                return 1

        # 用户有实体，直接更新时间戳
        result = ts_service.set_sync_timestamp(entity_id, target_date)

        if result.success:
            self._print_timestamp_success(user["screen_name"], target_date, time_desc)
            return 0
        else:
            print(f"❌ {result.error}")
            return 1

    def _handle_list_timestamp(
        self,
        target_id: str,
        target_date: Optional[datetime],
        time_desc: str,
        force: bool,
        db_service: "DatabaseService",
        ts_service: "TimestampService",
    ) -> int:
        """处理列表时间戳设置（支持自动创建）"""
        if not target_id.isdigit():
            print("列表ID必须是数字")
            return 1

        list_id_int = int(target_id)

        list_exists = db_service.check_list_exists(list_id_int)

        if not list_exists:
            # 列表不存在，尝试自动创建（与用户路径对称）
            print(f"列表 {target_id} 不在数据库中，尝试自动创建...")
            result = ts_service.get_or_create_list_entity(list_id_int, target_date)

            if result.success:
                print(f"✅ {result.message}")
                return 0
            else:
                print(f"❌ {result.error}")
                print("可能原因：列表ID不存在、网络问题或 TMD 配置错误")
                return 1

        # 列表已存在，执行批量设置
        if not force:
            print(f"警告：这将修改列表 {target_id} 中所有成员的时间戳！")
        print(f"正在处理列表 {target_id}（包含所有成员）...")
        if target_date:
            print(f"   将设置所有成员从 {time_desc} 开始同步")
        else:
            print("   将重置所有成员为全量下载模式")

        result = ts_service.batch_set_list_timestamp(list_id_int, target_date)

        if result.success:
            print(f"✅ {result.message}")
            if result.failed_items:
                print(f"⚠️  失败项目: {', '.join(result.failed_items[:5])}")
                if len(result.failed_items) > 5:
                    print(f"   ... 还有 {len(result.failed_items) - 5} 个")
            return 0
        else:
            print(f"❌ {result.error}")
            return 1

    # ==================== CLI 主入口方法 ====================

    def _set_headless_mode(self, enabled: bool) -> None:
        """
        设置无头模式

        Args:
            enabled: 是否启用无头模式
        """
        self.container.ui.headless_mode = enabled

    def handle_auto_mode(self, args: argparse.Namespace) -> int:
        """
        处理 --auto-q 参数，自动下载所有配置的固定列表

        Args:
            args: 解析后的命令行参数

        Returns:
            int: 退出码（0=成功，1=失败）
        """
        quick_list_ids = self.config.quick_list_ids
        if not quick_list_ids:
            print("❌ 未配置固定列表，请先在配置中设置 quick_list_ids")
            return 1

        print(f"📝 开始自动下载 {len(quick_list_ids)} 个固定列表...")

        failed_lists = []
        for i, list_id in enumerate(quick_list_ids, 1):
            print(f"📝 下载固定列表 {i}/{len(quick_list_ids)}: {list_id}")
            result = self.download_service.download_list(list_id)
            if not result.success:
                failed_lists.append(list_id)

        if failed_lists:
            print(f"\n❌ {len(failed_lists)} 个列表下载失败: {', '.join(failed_lists)}")
            return 1

        print("\n✅ 所有固定列表下载完成！")
        return 0

    def handle_file_mode(self, args: argparse.Namespace) -> int:
        """
        处理 --file 参数，从文件批量导入

        Args:
            args: 解析后的命令行参数

        Returns:
            int: 退出码（0=成功，1=失败）
        """
        file_path = args.file
        if not file_path.exists():
            print(f"❌ 文件不存在: {file_path}")
            return 1

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"❌ 读取文件失败: {e}")
            return 1

        if not lines:
            print("❌ 文件为空")
            return 1

        print(f"📝 从文件读取到 {len(lines)} 行")

        all_parsed = []
        for line in lines:
            parsed = InputParser.parse_batch(line)
            all_parsed.extend(parsed)

        if not all_parsed:
            print("❌ 未能解析任何有效输入")
            return 1

        users = [v for t, v in all_parsed if t == "user"]
        lists = [v for t, v in all_parsed if t == "list"]

        print(f"📝 解析结果: {len(users)} 个用户, {len(lists)} 个列表")

        if not self.container.ui.headless_mode:
            confirm = input("\n确认执行? [Y/N]: ").strip().upper()
            if confirm != "Y":
                print("已取消")
                return 1

        failed = []
        for user in users:
            print(f"\n📝 下载用户: @{user}")
            result = self.download_service.download_user(user, source="CLI 文件导入")
            if not result.success:
                failed.append(user)
                print(result.get_error_message())
            else:
                print(result.get_success_message())

        for list_id in lists:
            print(f"\n📝 下载列表: {list_id}")
            result = self.download_service.download_list(list_id)
            if not result.success:
                failed.append(list_id)
                print(result.get_error_message())
            else:
                print(result.get_success_message())

        if failed:
            print(f"\n❌ {len(failed)} 个任务失败: {', '.join(failed)}")
            return 1

        print("\n✅ 全部完成")
        return 0

    def handle_combo_mode(self, args: argparse.Namespace) -> int:
        """
        处理 --combo 参数，解析组合任务并执行

        Args:
            args: 解析后的命令行参数

        Returns:
            int: 退出码（0=成功，1=失败）
        """
        combo_input = args.combo
        if not combo_input:
            print("❌ 组合任务输入为空")
            return 1

        print(f"📝 解析组合任务: {combo_input}")

        parsed = InputParser.parse_batch(combo_input)
        if not parsed:
            print("❌ 无法解析输入")
            return 1

        failed = []
        for type_, value in parsed:
            if type_ == "user":
                print(f"\n📝 下载用户: @{value}")
                result = self.download_service.download_user(value, source="CLI 组合模式")
                if not result.success:
                    failed.append(value)
                    print(result.get_error_message())
                else:
                    print(result.get_success_message())
            elif type_ == "list":
                print(f"\n📝 下载列表: {value}")
                result = self.download_service.download_list(value)
                if not result.success:
                    failed.append(value)
                    print(result.get_error_message())
                else:
                    print(result.get_success_message())

        if not failed:
            print("\n✅ 组合任务全部完成！")
            return 0
        else:
            print(f"\n❌ 部分任务失败: {', '.join(failed)}")
            return 1

    def handle_resume_mode(self, args: argparse.Namespace) -> int:
        """
        处理 -r 恢复下载

        Args:
            args: 解析后的命令行参数

        Returns:
            int: 退出码（0=成功，1=失败）
        """
        remedy_service = self.container.resolve("remedy_service")

        if self.container.ui.headless_mode:
            return self._run_headless_resume(remedy_service)
        else:
            print("📝 正在从数据库恢复所有待处理下载...")
            exit_code, _, _ = self.download_service.run_tmd(args=[])

            if exit_code == 0:
                print("✅ 恢复下载完成！")
                return 0
            else:
                print("❌ 恢复下载失败")
                print("📝 可随时恢复 - 已下载的文件是安全的")
                print("💡 使用 [R] 恢复下载 可续传未完成任务")
                return 1

    def _run_headless_resume(self, remedy_service) -> int:
        """
        无头模式下的自动恢复下载

        Args:
            remedy_service: 补救服务实例

        Returns:
            int: 退出码
        """
        import time

        round_count = 0
        last_pending = None
        stagnant_count = 0

        print("\n✅ 已开启自动循环模式（结束后将执行补救下载）")

        while True:
            round_count += 1
            print(f"\n🔄 第 {round_count} 轮恢复...")

            print("📝 正在从数据库恢复所有待处理下载...")
            exit_code, _, _ = self.download_service.run_tmd(args=[])

            if exit_code == 0:
                print("✅ 当前轮次下载完成！")
            else:
                print("❌ 当前轮次下载失败")

            pending = self.download_service.check_pending_tweets(self.config.root_path)

            if pending is None or pending == 0:
                print("\n✅ 所有待处理下载已完成！")
                return 0

            print(f"\n📝 仍有 {pending} 个待处理推文")

            if pending == last_pending:
                stagnant_count += 1
                if stagnant_count >= C.RESUME_MAX_STAGNANT - 1:
                    print(f"\n⚠️ 连续 {C.RESUME_MAX_STAGNANT} 轮待处理数量未变化")
                    print("📝 自动循环结束，准备执行补救下载...")
                    break
            else:
                stagnant_count = 0

            last_pending = pending

            if round_count >= C.RESUME_MAX_ROUNDS:
                print(f"\n⚠️ 已达到最大轮数限制 ({C.RESUME_MAX_ROUNDS} 轮)")
                print("📝 自动循环结束，准备执行补救下载...")
                break

            self.container.ui.delay(seconds=C.RESUME_RETRY_SEC, message=f"⏳ {C.RESUME_RETRY_SEC}秒后继续下一轮...", show_countdown=False)

        # 执行补救下载
        print("\n🔄 开始补救下载（绕开TMD）...")
        from ..ui.remedy_progress import SilentProgressCallback

        callback = SilentProgressCallback()
        success = remedy_service.execute(progress_callback=callback)
        return 0 if success else 1

    def handle_single_download(self, args: argparse.Namespace) -> int:
        """
        处理 -u/-l/-f 单目标下载

        Args:
            args: 解析后的命令行参数

        Returns:
            int: 退出码（0=成功，1=失败）
        """
        if args.user:
            username = clean_username(args.user)
            if not username:
                print(f"❌ 无效的用户名: {args.user}")
                return 1

            print(f"📝 开始下载用户: @{username}")
            result = self.download_service.download_user(username)

            if result.success:
                print(result.get_success_message())
                return 0
            else:
                print(result.get_error_message())
                self._print_result_errors(result)
                return 1

        elif args.list:
            list_id = args.list.strip()
            if not list_id.isdigit() or len(list_id) < C.LIST_ID_MIN_LEN:
                print(f"❌ 无效的列表ID: {list_id}")
                print(f"列表ID应为 {C.LIST_ID_MIN_LEN} 位以上数字")
                return 1

            print(f"📝 开始下载列表: {list_id}")
            result = self.download_service.download_list(list_id)
            if result.success:
                print(result.get_success_message())
                return 0
            else:
                print(result.get_error_message())
                self._print_result_errors(result)
                return 1

        elif args.foll:
            username = clean_username(args.foll)
            if not username:
                print(f"❌ 无效的用户名: {args.foll}")
                return 1

            print(f"📝 开始下载 @{username} 的关注列表")
            exit_code, _, _ = self.download_service.run_tmd(args=["--following", username])

            if exit_code == 0:
                print(f"✅ @{username} 关注列表下载完成")
                return 0
            else:
                print(f"❌ @{username} 关注列表下载失败")
                return 1

        return 1

    def handle_profile_download(self, args: argparse.Namespace) -> int:
        """
        处理 --profile-user/--profile-list 参数

        Args:
            args: 解析后的命令行参数

        Returns:
            int: 退出码（0=成功，1=失败）
        """
        if args.profile_user:
            for username in args.profile_user:
                clean_name = clean_username(username)
                if not clean_name:
                    print(f"⚠️ 跳过无效用户名: {username}")
                    continue

                print(f"📝 下载用户 Profile: @{clean_name}")
                exit_code, _, _ = self.download_service.run_tmd(
                    args=["--user", clean_name]
                )

                if exit_code == 0:
                    print(f"✅ @{clean_name} Profile 下载完成")
                else:
                    print(f"❌ @{clean_name} Profile 下载失败")

        if args.profile_list:
            for list_id in args.profile_list:
                if not list_id.isdigit() or len(list_id) < C.LIST_ID_MIN_LEN:
                    print(f"⚠️ 跳过无效列表ID: {list_id}")
                    continue

                print(f"📝 下载列表成员 Profile: {list_id}")
                exit_code, _, _ = self.download_service.run_tmd(
                    args=["--list", list_id]
                )

                if exit_code == 0:
                    print(f"✅ 列表 {list_id} Profile 下载完成")
                else:
                    print(f"❌ 列表 {list_id} Profile 下载失败")

        return 0

    def _print_result_errors(self, result) -> None:
        """
        打印下载错误信息

        Args:
            result: 下载结果
        """
        warn_users = getattr(result, "warn_users", None) or []
        if warn_users:
            users_str = " ".join(warn_users[:5])
            print(f"⚠️ 警告用户: {users_str}")
            if len(warn_users) > 5:
                print(f"   ... 还有 {len(warn_users) - 5} 个")

        error_messages = getattr(result, "error_messages", None) or []
        if error_messages:
            error_count = getattr(result, "error_count", len(error_messages))
            print(f"❌ 错误信息 ({error_count} 个):")
            for err in error_messages[:3]:
                print(f"   - {err[:80]}")


__all__ = ["CLIHandler"]
