# -*- coding: utf-8 -*-
"""
时间戳服务模块

提供时间戳格式化和设置功能。
采用智能选择操作方式：已存在实体直接数据库操作，不存在则通过 TMD 创建。

主要功能：
- 时间戳格式化显示
- 同步时间戳设置（智能选择数据库操作或 TMD 命令）
- 批量列表时间戳设置
- 自动创建用户/列表实体
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, List, Optional, Tuple

if TYPE_CHECKING:
    import logging

    from ..config.config import TMDConfig
    from .database_service import DatabaseService
    from .download_service import DownloadService

from ..tmd_types import BatchOperationResult, OperationResult
from ..utils.formatters import format_duration, format_timestamp


class TimestampService:
    """时间戳服务。

    提供时间戳业务逻辑协调功能。
    采用智能选择操作方式：已存在实体直接数据库操作，不存在则通过 TMD 创建。

    Attributes:
        config: 配置实例
        logger: 日志实例
        database_service: 数据库服务实例（用于数据库操作）
        download_service: 下载服务实例（用于调用 TMD 创建新实体）
    """

    def __init__(
        self,
        config: "TMDConfig",
        logger: "logging.Logger",
        database_service: "DatabaseService",
        download_service: Optional["DownloadService"] = None,
    ) -> None:
        """初始化时间戳服务

        Args:
            config: 配置实例
            logger: 日志实例
            database_service: 数据库服务实例
            download_service: 下载服务实例（用于调用 TMD --mark-downloaded）
        """
        self.config = config
        self.logger = logger
        self.database_service = database_service
        self.download_service = download_service

    # ==================== 时间戳设置（智能选择） ====================

    def set_sync_timestamp(
        self,
        entity_id: int,
        target_date: Optional[datetime],
    ) -> OperationResult:
        """设置同步时间戳（直接数据库操作）

        由于调用此方法时实体必然已存在，直接操作数据库更高效。

        Args:
            entity_id: 用户实体 ID
            target_date: 目标时间戳，None 表示重置为全量下载

        Returns:
            OperationResult: 操作结果
        """
        success, screen_name = self.database_service.set_user_timestamp(entity_id, target_date)

        if success and screen_name:
            ts_str = target_date.strftime("%Y-%m-%d %H:%M:%S") if target_date else "全量下载"
            return OperationResult(
                success=True,
                message=f"已设置 @{screen_name} 的时间戳为: {ts_str}",
                data={"screen_name": screen_name, "timestamp": ts_str},
            )
        return OperationResult(success=False, error=f"实体 ID {entity_id} 不存在或设置失败")

    def get_or_create_user_entity(
        self,
        screen_name: str,
        target_date: Optional[datetime] = None,
    ) -> OperationResult:
        """获取或创建用户实体并设置时间戳（智能选择）

        如果用户已存在，直接操作数据库设置时间戳。
        如果用户不存在，通过 TMD 创建实体并设置时间戳。

        Args:
            screen_name: 用户名
            target_date: 目标时间戳，None 表示全量下载

        Returns:
            OperationResult: 操作结果，data 包含用户信息
        """
        user_info = self.database_service.get_user_entity_info(screen_name)

        if user_info and user_info.get("entity_id"):
            entity_id = user_info["entity_id"]
            success, _ = self.database_service.set_user_timestamp(entity_id, target_date)
            if success:
                ts_str = target_date.strftime("%Y-%m-%d %H:%M:%S") if target_date else "全量下载"
                return OperationResult(
                    success=True,
                    message=f"已设置 @{screen_name} 的时间戳为: {ts_str}",
                    data=user_info,
                )
            return OperationResult(success=False, error="设置时间戳失败")

        if self.download_service is None:
            return OperationResult(
                success=False, error=f"用户 @{screen_name} 不存在，需要先下载一次"
            )

        return self._create_user_via_tmd(screen_name, target_date)

    def get_or_create_list_entity(
        self,
        list_id: int,
        target_date: Optional[datetime] = None,
    ) -> OperationResult:
        """获取或创建列表实体并设置时间戳（智能选择）

        如果列表已存在，直接操作数据库设置时间戳。
        如果列表不存在，通过 TMD 创建实体并设置时间戳。

        Args:
            list_id: 列表 ID
            target_date: 目标时间戳，None 表示全量下载

        Returns:
            OperationResult: 操作结果
        """
        if self.database_service.check_list_entity_exists(list_id):
            success = self.database_service.set_list_timestamp(list_id, target_date)
            if success:
                ts_str = target_date.strftime("%Y-%m-%d %H:%M:%S") if target_date else "全量下载"
                return OperationResult(
                    success=True,
                    message=f"已设置列表 {list_id} 的时间戳为: {ts_str}",
                    data={"list_id": list_id, "timestamp": ts_str},
                )
            return OperationResult(success=False, error="设置时间戳失败")

        if self.download_service is None:
            return OperationResult(success=False, error=f"列表 {list_id} 不存在，需要先下载一次")

        return self._create_list_via_tmd(list_id, target_date)

    # ==================== TMD 调用方法 ====================

    def batch_set_list_timestamp(
        self,
        list_id: int,
        target_date: Optional[datetime],
    ) -> BatchOperationResult:
        """批量设置列表中所有用户的时间戳

        通过 TMD --list --mark-downloaded 实现，TMD 会自动处理列表中的所有用户。
        这比逐个用户调用更高效，且与 TMD 原生行为一致。

        Args:
            list_id: 列表 ID
            target_date: 目标时间戳，None 表示重置为全量下载

        Returns:
            BatchOperationResult: 批量操作结果
        """
        if self.download_service is None:
            return BatchOperationResult(
                success=False,
                error="下载服务不可用，无法设置时间戳",
                total=0,
                success_count=0,
                failed_count=0,
            )

        tmd_args = ["-list", str(list_id), "-mark-downloaded"]
        if target_date is not None:
            mark_time = target_date.strftime("%Y-%m-%dT%H:%M:%S")
            tmd_args.extend(["-mark-time", mark_time])
        else:
            tmd_args.extend(["-mark-time", "null"])

        exit_code, stdout, stderr = self.download_service.run_tmd(args=tmd_args)

        if exit_code != 0:
            error_msg = stderr if stderr else f"设置列表 {list_id} 时间戳失败"
            return BatchOperationResult(
                success=False, error=error_msg, total=0, success_count=0, failed_count=0
            )

        success_count, failed_count, failed_items = self._parse_tmd_mark_results(stdout)

        total = success_count + failed_count
        ts_str = target_date.strftime("%Y-%m-%d %H:%M:%S") if target_date else "全量下载"

        if success_count == 0 and total == 0:
            message = f"已设置列表 {list_id} 的时间戳为: {ts_str}"
        elif failed_count > 0:
            message = f"部分成功: {success_count}/{total} 个用户，时间戳: {ts_str}"
        else:
            message = f"成功处理 {success_count} 个用户，时间戳: {ts_str}"

        return BatchOperationResult(
            success=True,
            message=message,
            total=total,
            success_count=success_count,
            failed_count=failed_count,
            failed_items=failed_items,
        )

    def _parse_tmd_mark_results(self, stdout: str) -> Tuple[int, int, List[str]]:
        """解析 TMD --mark-downloaded 的输出结果

        解析格式：
        === MARK_DOWNLOADED_RESULTS ===
        ENTITY_ID:1|USER_ID:44196397|SCREEN_NAME:elonmusk|STATUS:OK
        === END_RESULTS ===

        Args:
            stdout: TMD 命令的标准输出

        Returns:
            (成功数, 失败数, 失败用户名列表)
        """
        success_count = 0
        failed_count = 0
        failed_items: List[str] = []

        in_results = False
        for line in stdout.split("\n"):
            line = line.strip()
            if line == "=== MARK_DOWNLOADED_RESULTS ===":
                in_results = True
                continue
            if line == "=== END_RESULTS ===":
                break
            if not in_results or not line.startswith("ENTITY_ID:"):
                continue

            parts = {}
            for part in line.split("|"):
                if ":" in part:
                    key, value = part.split(":", 1)
                    parts[key] = value

            screen_name = parts.get("SCREEN_NAME", "")
            status = parts.get("STATUS", "")

            if status == "OK":
                success_count += 1
            else:
                failed_count += 1
                if screen_name:
                    failed_items.append(screen_name)

        return success_count, failed_count, failed_items

    def _create_user_via_tmd(
        self,
        screen_name: str,
        target_date: Optional[datetime] = None,
    ) -> OperationResult:
        """通过 TMD 创建用户实体

        Args:
            screen_name: 用户名
            target_date: 目标时间戳

        Returns:
            OperationResult: 操作结果，data 包含用户信息
        """
        if self.download_service is None:
            return OperationResult(success=False, error="下载服务不可用，无法创建用户")

        tmd_args = ["-user", screen_name, "-mark-downloaded"]
        if target_date is not None:
            mark_time = target_date.strftime("%Y-%m-%dT%H:%M:%S")
            tmd_args.extend(["-mark-time", mark_time])
        else:
            tmd_args.extend(["-mark-time", "null"])

        exit_code, _, _ = self.download_service.run_tmd(args=tmd_args)

        if exit_code != 0:
            return OperationResult(success=False, error=f"通过 TMD 创建用户 @{screen_name} 失败")

        time.sleep(0.3)

        user_info = self.database_service.get_user_entity_info(screen_name)
        if not user_info or not user_info.get("entity_id"):
            return OperationResult(success=False, error=f"TMD 创建后仍找不到用户 @{screen_name}")

        ts_str = target_date.strftime("%Y-%m-%d %H:%M:%S") if target_date else "全量下载"
        return OperationResult(
            success=True, message=f"已创建 @{screen_name}，时间戳: {ts_str}", data=user_info
        )

    def _create_list_via_tmd(
        self,
        list_id: int,
        target_date: Optional[datetime] = None,
    ) -> OperationResult:
        """通过 TMD 创建列表实体

        Args:
            list_id: 列表 ID
            target_date: 目标时间戳

        Returns:
            OperationResult: 操作结果
        """
        if self.download_service is None:
            return OperationResult(success=False, error="下载服务不可用，无法创建列表")

        tmd_args = ["-list", str(list_id), "-mark-downloaded"]
        if target_date is not None:
            mark_time = target_date.strftime("%Y-%m-%dT%H:%M:%S")
            tmd_args.extend(["-mark-time", mark_time])
        else:
            tmd_args.extend(["-mark-time", "null"])

        exit_code, _, _ = self.download_service.run_tmd(args=tmd_args)

        if exit_code != 0:
            return OperationResult(success=False, error=f"通过 TMD 创建列表 {list_id} 失败")

        time.sleep(0.3)

        if not self.database_service.check_list_entity_exists(list_id):
            return OperationResult(success=False, error=f"TMD 创建后仍找不到列表 {list_id}")

        ts_str = target_date.strftime("%Y-%m-%d %H:%M:%S") if target_date else "全量下载"
        return OperationResult(
            success=True,
            message=f"已创建列表 {list_id}，时间戳: {ts_str}",
            data={"list_id": list_id, "timestamp": ts_str},
        )


__all__ = ["TimestampService"]
