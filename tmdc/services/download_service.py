# -*- coding: utf-8 -*-
"""
TMD 下载服务模块

提供 TMD 下载操作的核心功能（纯业务逻辑，无 UI 依赖）。
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional, Tuple

if TYPE_CHECKING:
    from tmdc.parsers.log_parser import TMDLogParser
    from tmdc.tmd_types import (
        IConfig,
        IDatabaseService,
        ILogger,
    )

from tmdc.tmd_types import DownloadResult


class DownloadService:
    """
    TMD 下载服务（纯业务逻辑，无 UI 依赖）

    提供 TMD 下载操作的核心功能，包括用户下载、列表下载等。
    所有输出由调用方（CLI/TUI）负责。

    Attributes:
        config: 配置实例
        logger: 日志实例
        executable_path: TMD 可执行文件路径
        log_parser: 日志解析器实例
        database_service: 数据库服务实例（可选）

    Example:
        >>> service = DownloadService(config, logger, Path("tmd.exe"), log_parser)
        >>> result = service.download_user("username")
        >>> print(f"下载成功: {result.success}")
    """

    def __init__(
        self,
        config: IConfig,
        logger: ILogger,
        executable_path: Optional[Path],
        log_parser: Optional[TMDLogParser],
        database_service: Optional[IDatabaseService] = None,
    ) -> None:
        """
        初始化下载服务

        Args:
            config: 配置实例
            logger: 日志实例
            executable_path: TMD 可执行文件路径
            log_parser: 日志解析器实例（可选，允许为 None）
            database_service: 数据库服务实例（可选，用于列表下载检查）
        """
        self.config = config
        self.logger = logger
        self.executable_path = executable_path
        self.log_parser = log_parser
        self.database_service = database_service

    def download_user(
        self,
        username: str,
        *,
        timestamp: Optional[str] = None,
        source: str = "",
    ) -> DownloadResult:
        """
        下载用户媒体（纯业务逻辑，无输出）

        Args:
            username: Twitter 用户名
            timestamp: 时间戳过滤（可选）
            source: 来源描述（可选）

        Returns:
            DownloadResult: 下载结果，包含所有信息
        """
        args = ["--user", f"@{username}"]
        log_desc = f"用户 @{username}"
        if source:
            log_desc += f" (来源: {source})"

        self.logger.info(f"执行下载: {log_desc}")

        exit_code, stdout, stderr = self.run_tmd(args)
        parse_result = self._parse_tmd_output(exit_code)

        return DownloadResult(
            exit_code=exit_code,
            warn_count=parse_result.warn_count,
            error_count=parse_result.error_count,
            warn_users=parse_result.warn_users,
            error_messages=parse_result.error_messages,
            raw_output=parse_result.raw_output,
            target_type="user",
            target_id=username,
            log_desc=log_desc,
        )

    def download_list(
        self,
        list_id: str,
        *,
        timestamp: Optional[str] = None,
    ) -> DownloadResult:
        """
        下载列表媒体（纯业务逻辑，无输出）

        Args:
            list_id: Twitter 列表 ID
            timestamp: 时间戳过滤（可选）

        Returns:
            DownloadResult: 下载结果，包含所有信息
        """
        args = ["--list", list_id]

        log_desc = f"列表 {list_id}"
        self.logger.info(f"执行下载: {log_desc}")

        exit_code, stdout, stderr = self.run_tmd(args)
        parse_result = self._parse_tmd_output(exit_code)

        return DownloadResult(
            exit_code=exit_code,
            warn_count=parse_result.warn_count,
            error_count=parse_result.error_count,
            warn_users=parse_result.warn_users,
            error_messages=parse_result.error_messages,
            raw_output=parse_result.raw_output,
            target_type="list",
            target_id=list_id,
            log_desc=log_desc,
        )

    def download_batch(
        self,
        users: Optional[List[str]] = None,
        lists: Optional[List[str]] = None,
    ) -> DownloadResult:
        """
        批量下载用户和列表（单次 TMD 调用）

        Args:
            users: 用户名列表
            lists: 列表 ID 列表

        Returns:
            DownloadResult: 下载结果
        """
        users = users or []
        lists = lists or []

        if not users and not lists:
            return DownloadResult(
                exit_code=0,
                warn_count=0,
                error_count=0,
                warn_users=[],
                error_messages=["无下载目标"],
                raw_output="",
                target_type="batch",
                target_id="",
                log_desc="批量下载（空）",
            )

        args: List[str] = []
        for user in users:
            args.extend(["--user", f"@{user}"])
        for list_id in lists:
            args.extend(["--list", list_id])

        targets_desc = []
        if users:
            targets_desc.append(f"{len(users)} 个用户")
        if lists:
            targets_desc.append(f"{len(lists)} 个列表")
        log_desc = f"批量下载: {', '.join(targets_desc)}"

        self.logger.info(f"执行下载: {log_desc}")

        exit_code, stdout, stderr = self.run_tmd(args)
        parse_result = self._parse_tmd_output(exit_code)

        return DownloadResult(
            exit_code=exit_code,
            warn_count=parse_result.warn_count,
            error_count=parse_result.error_count,
            warn_users=parse_result.warn_users,
            error_messages=parse_result.error_messages,
            raw_output=parse_result.raw_output,
            target_type="batch",
            target_id="",
            log_desc=log_desc,
        )

    def run_tmd(
        self,
        args: List[str],
        *,
        capture_output: bool = False,
        timeout: Optional[int] = None,
    ) -> Tuple[int, str, str]:
        """
        执行 TMD 命令

        Args:
            args: 命令行参数
            capture_output: 是否捕获输出
            timeout: 超时时间（秒）

        Returns:
            (退出码, 标准输出, 标准错误)
        """
        if not self.executable_path:
            err_msg = "错误：找不到 TMD 可执行文件"
            self.logger.error(err_msg)
            return 1, "", err_msg

        cmd = [str(self.executable_path)] + args
        env = self._set_proxy_env()

        try:
            if capture_output:
                with subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="ignore",
                    env=env,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                ) as process:
                    try:
                        stdout, stderr = process.communicate(timeout=timeout)
                        self._log_command(args, process.returncode, stdout, stderr)
                        return process.returncode, stdout, stderr
                    except subprocess.TimeoutExpired:
                        process.kill()
                        return 124, "", "执行超时"
            else:
                process = subprocess.Popen(
                    cmd,
                    env=env,
                    stdout=sys.stdout,
                    stderr=sys.stderr,
                    encoding="utf-8",
                    errors="ignore",
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                )

                exit_code = process.wait()
                self._log_command(args, exit_code)
                return exit_code, "", ""

        except OSError:
            import traceback

            self.logger.critical(f"[TMD执行] 系统级错误:\n{traceback.format_exc()}")
            raise
        except Exception as e:
            import traceback

            self.logger.error(f"[TMD执行] 异常详情:\n{traceback.format_exc()}")
            return 1, "", str(e)



    def check_pending_tweets(self, root_path: Optional[str]) -> Optional[int]:
        """
        检查待处理推文数量

        Args:
            root_path: 下载根目录路径

        Returns:
            待处理推文数量，如果读取失败返回 None
        """
        import json

        if not root_path:
            return 0

        errors_path = Path(root_path) / ".data" / "errors.json"
        if not errors_path.exists():
            return 0

        try:
            with open(errors_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            total = sum(len(tweets) for tweets in data.values() if isinstance(tweets, list))
            return total if total > 0 else 0
        except json.JSONDecodeError:
            self.logger.warning("errors.json 格式错误")
            return None
        except Exception as e:
            self.logger.warning(f"检查待处理推文失败: {e}")
            return None

    def _parse_tmd_output(self, exit_code: int) -> DownloadResult:
        """
        解析 TMD 输出（纯逻辑，无输出）

        Args:
            exit_code: TMD 退出码

        Returns:
            DownloadResult: 解析结果
        """
        if self.log_parser is None:
            return DownloadResult(exit_code=exit_code)

        log_start_pos = self.log_parser.get_size()
        result = self.log_parser.parse_increment(log_start_pos)
        result.exit_code = exit_code
        return result

    def check_list_exists(self, list_id: str) -> bool:
        """检查列表是否已存在于数据库中

        Args:
            list_id: 列表 ID

        Returns:
            列表存在返回 True，否则返回 False
        """
        if self.database_service is None:
            return False

        try:
            return self.database_service.check_list_metadata_exists(int(list_id))
        except (ValueError, AttributeError):
            return False

    def _set_proxy_env(self) -> dict:
        """
        设置代理环境变量

        Returns:
            环境变量字典
        """
        env = os.environ.copy()
        if self.config.use_proxy and self.config.proxy_hostname:
            env["HTTP_PROXY"] = f"http://{self.config.proxy_hostname}:{self.config.proxy_tcp_port}"
            env["HTTPS_PROXY"] = f"http://{self.config.proxy_hostname}:{self.config.proxy_tcp_port}"
        else:
            for key in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]:
                env.pop(key, None)
        return env

    def _log_command(
        self, args: List[str], exit_code: int, stdout: str = "", stderr: str = ""
    ) -> None:
        """
        记录命令执行日志（安全加固）

        Args:
            args: 命令行参数
            exit_code: 退出码
            stdout: 标准输出
            stderr: 标准错误
        """
        safe_args = []
        hide_next = False
        sensitive_flags = {"--auth-token", "--ct0", "-t"}

        for arg in args:
            if hide_next:
                safe_args.append("***")
                hide_next = False
                continue

            if "=" in arg:
                parts = arg.split("=", 1)
                if parts[0] in sensitive_flags:
                    safe_args.append(f"{parts[0]}=***")
                    continue

            if len(arg) > 2 and arg.startswith("-t") and not arg.startswith("--"):
                safe_args.append("-t***")
                continue

            if arg in sensitive_flags:
                safe_args.append(arg)
                hide_next = True
            else:
                safe_args.append(arg)

        self.logger.info(f"执行命令: tmd {' '.join(safe_args)}")
        self.logger.info(f"退出码: {exit_code}")

        if exit_code != 0 and stderr:
            err_msg = stderr[:500] if len(stderr) > 500 else stderr
            self.logger.error(f"错误输出: {err_msg}")


__all__ = ["DownloadService"]
