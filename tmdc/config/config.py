#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块

负责配置的加载、保存和验证。
"""

from __future__ import annotations

# 标准库
import copy
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    pass

# 第三方库（无）

try:
    import yaml
except ImportError:
    yaml = None

# 本地模块
from tmdc.utils.file_io import atomic_write_yaml
from tmdc.utils.validators.proxy import check_proxy_values


@dataclass
class TMDConfig:
    """
    TMD 配置：Windows 专用

    管理所有 TMD 相关配置，包括代理、Cookie、下载参数等。

    """

    # TMD 可执行文件名
    tmd_exe_names: List[str] = field(default_factory=lambda: ["tmd.exe", "tmd"])

    # 代理配置
    proxy_hostname: str = "127.0.0.1"
    proxy_tcp_port: int = 7897
    use_proxy: bool = True

    # 快速列表
    quick_list_ids: List[str] = field(default_factory=list)

    # v4.7.10 保留：文件分批大小配置（防卡顿保护）
    file_batch_size: int = 3

    # v4.7.10 变更：双轨风控延迟配置（区分成功/失败）
    batch_delay_success_min: int = 0
    batch_delay_success_max: int = 0
    batch_delay_fail_min: int = 0
    batch_delay_fail_max: int = 0

    # 日志配置
    log_level: str = "INFO"
    log_max_bytes: int = 2 * 1024 * 1024
    log_backup_count: int = 2

    # 自定义配置路径
    custom_config_path: Optional[Path] = field(default=None, repr=False)

    # v4.8.0 新增：TMD 核心配置字段
    root_path: Optional[str] = None
    auth_token: Optional[str] = None
    ct0: Optional[str] = None
    max_download_routine: int = 0

    # v4.8.1 新增：列表间间隔（0-300秒）
    quick_list_interval: int = 12

    def __post_init__(self) -> None:
        """初始化后处理"""
        # 设置配置文件路径
        if self.custom_config_path:
            self.config_file = Path(self.custom_config_path)
            self.config_dir = self.config_file.parent
        else:
            appdata = os.environ.get("APPDATA", str(Path.home()))
            self.config_dir = Path(appdata) / ".tmd2"
            self.config_file = self.config_dir / "conf.yaml"

        # 设置其他路径
        self.log_dir = self.config_dir
        self.cookie_file = self.config_dir / "additional_cookies.yaml"
        self.log_file = self.log_dir / "tmd_controller.log"

        # 加载配置
        config = self._read_config()
        self._load_all_configs(config)

    # ==================== 属性 ====================

    @property
    def default_quick_list_id(self) -> Optional[str]:
        """获取默认快速列表 ID"""
        return self.quick_list_ids[0] if self.quick_list_ids else None

    @property
    def is_batch_delay_success_enabled(self) -> bool:
        """检查成功延迟是否启用"""
        return self.batch_delay_success_max > 0

    @property
    def is_batch_delay_fail_enabled(self) -> bool:
        """检查失败延迟是否启用"""
        return self.batch_delay_fail_max > 0

    @property
    def db_path(self) -> Optional[Path]:
        """获取数据库路径"""
        if self.root_path:
            return Path(self.root_path) / ".data" / "foo.db"
        return None



    # ==================== 配置读取方法 ====================

    def _read_config(self) -> Dict[str, Any]:
        """通用配置读取方法"""
        if not yaml or not self.config_file.exists():
            return {}
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}

    def _get_logger(self) -> "logging.Logger":
        """获取日志记录器"""
        import logging

        return logging.getLogger("TMDController")

    def _load_all_configs(self, config: Dict[str, Any]) -> None:
        """集中加载所有配置项"""
        if not config:
            return

        self._load_proxy_from_config(config)
        self._load_quick_lists_from_config(config)
        self._load_batch_config_from_config(config)
        self._load_batch_delay_config(config)
        self._load_core_config_from_config(config)
        self._load_quick_list_interval(config)

    def _load_proxy_from_config(self, config: Dict[str, Any]) -> None:
        """从配置加载代理设置"""
        try:
            new_host = config.get("proxy_hostname", self.proxy_hostname)
            new_port = config.get("proxy_tcp_port", self.proxy_tcp_port)
            new_use = config.get("use_proxy", self.use_proxy)

            is_valid, error = check_proxy_values(new_host, new_port, new_use)
            if is_valid:
                self.proxy_hostname = new_host
                self.proxy_tcp_port = int(new_port) if isinstance(new_port, str) else new_port
                self.use_proxy = new_use
            else:
                self._get_logger().warning(f"配置文件代理值无效({error})，使用默认值")
        except Exception as e:
            self._get_logger().warning(f"加载代理配置失败（使用默认）: {e}")

    def _load_quick_lists_from_config(self, config: Dict[str, Any]) -> None:
        """从配置加载固定列表配置"""
        try:
            if "quick_list_ids" in config and isinstance(config["quick_list_ids"], list):
                valid_ids = []
                for item in config["quick_list_ids"]:
                    if isinstance(item, (str, int)):
                        s = str(item).strip()
                        if s.isdigit() and len(s) >= 10:
                            valid_ids.append(s)

                if valid_ids:
                    self.quick_list_ids = valid_ids
                    self._get_logger().info(f"已加载 {len(valid_ids)} 个固定列表")
        except Exception as e:
            self._get_logger().warning(f"加载固定列表配置失败: {e}")

    def _load_batch_config_from_config(self, config: Dict[str, Any]) -> None:
        """从配置加载文件分批配置"""
        try:
            if "file_batch_size" in config:
                size = config["file_batch_size"]
                if isinstance(size, int) and 1 <= size <= 50:
                    self.file_batch_size = size
                    self._get_logger().info(f"已加载文件分批大小: {size}")
                else:
                    self._get_logger().warning(
                        f"配置文件 file_batch_size 无效({size})，使用默认值3"
                    )
        except Exception as e:
            self._get_logger().warning(f"加载分批配置失败: {e}")

    def _load_batch_delay_config(self, config: Dict[str, Any]) -> None:
        """从配置加载双轨延迟配置"""
        if not config or "batch_delay" not in config:
            return

        try:
            delay_config = config["batch_delay"]
            if not isinstance(delay_config, dict):
                return

            success_cfg = delay_config.get("success", {})
            if isinstance(success_cfg, dict):
                s_min = success_cfg.get("min", 0)
                s_max = success_cfg.get("max", 0)
                if isinstance(s_min, (int, float)) and isinstance(s_max, (int, float)):
                    self.batch_delay_success_min = max(0, int(s_min))
                    self.batch_delay_success_max = max(0, int(s_max))
                    if self.batch_delay_success_min > self.batch_delay_success_max:
                        self.batch_delay_success_min, self.batch_delay_success_max = (
                            self.batch_delay_success_max,
                            self.batch_delay_success_min,
                        )

            fail_cfg = delay_config.get("fail", {})
            if isinstance(fail_cfg, dict):
                f_min = fail_cfg.get("min", 0)
                f_max = fail_cfg.get("max", 0)
                if isinstance(f_min, (int, float)) and isinstance(f_max, (int, float)):
                    self.batch_delay_fail_min = max(0, int(f_min))
                    self.batch_delay_fail_max = max(0, int(f_max))
                    if self.batch_delay_fail_min > self.batch_delay_fail_max:
                        self.batch_delay_fail_min, self.batch_delay_fail_max = (
                            self.batch_delay_fail_max,
                            self.batch_delay_fail_min,
                        )

            if self.is_batch_delay_success_enabled:
                self._get_logger().info(
                    f"已加载成功延迟: {self.batch_delay_success_min}-{self.batch_delay_success_max}秒"
                )
            if self.is_batch_delay_fail_enabled:
                self._get_logger().info(
                    f"已加载失败延迟: {self.batch_delay_fail_min}-{self.batch_delay_fail_max}秒"
                )
        except Exception as e:
            self._get_logger().warning(f"加载延迟配置失败: {e}")

    def _load_core_config_from_config(self, config: Dict[str, Any]) -> None:
        """从配置加载 TMD 核心配置（root_path, auth_token, ct0, max_download_routine）"""
        try:
            if "root_path" in config:
                self.root_path = config["root_path"]

            if "cookie" in config and isinstance(config["cookie"], dict):
                self.auth_token = config["cookie"].get("auth_token", self.auth_token)
                self.ct0 = config["cookie"].get("ct0", self.ct0)

            if "max_download_routine" in config:
                routine = config["max_download_routine"]
                if isinstance(routine, int) and routine >= 0:
                    self.max_download_routine = routine

            if self.auth_token and self.ct0:
                self._get_logger().info("已从配置加载 TMD 核心凭证")
        except Exception as e:
            self._get_logger().warning(f"加载核心配置失败: {e}")

    def _load_quick_list_interval(self, config: Dict[str, Any]) -> None:
        """加载列表间间隔"""
        if "quick_list_interval" in config:
            interval = config["quick_list_interval"]
            if isinstance(interval, int) and 0 <= interval <= 300:
                self.quick_list_interval = interval

    # ==================== 配置保存方法 ====================

    def save_quick_list_ids(self, new_ids: Optional[List[str]] = None) -> Tuple[bool, str]:
        """事务性保存固定列表到 conf.yaml"""
        old_ids = copy.deepcopy(self.quick_list_ids)
        target_ids = new_ids if new_ids is not None else old_ids

        success, error = self._save_config_field(
            field_path="quick_list_ids",
            new_value=target_ids,
            log_msg=f"固定列表已保存: {len(target_ids)} 个",
        )

        if success:
            self.quick_list_ids = copy.deepcopy(target_ids)
        else:
            self.quick_list_ids = old_ids

        return success, error

    def _save_config_field(
        self,
        field_path: str,
        new_value: Any,
        log_msg: str = "",
    ) -> Tuple[bool, str]:
        """
        保存配置字段（原子写入）

        Args:
            field_path: 字段路径（支持点号分隔的嵌套路径）
            new_value: 新值
            log_msg: 日志消息

        Returns:
            (成功标志, 错误消息)
        """
        try:
            # 读取现有配置
            config = self._read_config()

            # 设置新值
            keys = field_path.split(".")
            current = config
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            current[keys[-1]] = new_value

            # 确保目录存在
            self.config_dir.mkdir(parents=True, exist_ok=True)

            # 原子写入文件
            if not atomic_write_yaml(self.config_file, config, self._get_logger()):
                return False, "文件写入失败"

            if log_msg:
                self._get_logger().info(log_msg)

            return True, ""

        except Exception as e:
            error_msg = f"保存配置失败: {e}"
            self._get_logger().error(error_msg)
            return False, error_msg

    def save_core_config(
        self,
        root_path: Optional[str] = None,
        auth_token: Optional[str] = None,
        ct0: Optional[str] = None,
        max_download_routine: Optional[int] = None,
        allow_partial: bool = False,
    ) -> Tuple[bool, str]:
        """
        保存核心配置（原子写入）

        Args:
            root_path: TMD 下载根目录
            auth_token: Twitter auth_token
            ct0: Twitter CSRF token
            max_download_routine: 最大并行下载数
            allow_partial: 是否允许部分保存（未使用，保持兼容性）

        Returns:
            (成功标志, 错误消息)
        """
        old_root_path = self.root_path
        old_auth_token = self.auth_token
        old_ct0 = self.ct0
        old_max_download_routine = self.max_download_routine

        try:
            config = self._read_config()

            if root_path is not None:
                config["root_path"] = root_path

            if auth_token is not None or ct0 is not None:
                if "cookie" not in config:
                    config["cookie"] = {}
                if auth_token is not None:
                    config["cookie"]["auth_token"] = auth_token
                if ct0 is not None:
                    config["cookie"]["ct0"] = ct0

            if max_download_routine is not None:
                config["max_download_routine"] = max_download_routine

            self.config_dir.mkdir(parents=True, exist_ok=True)

            if not atomic_write_yaml(self.config_file, config, self._get_logger()):
                return False, "文件写入失败"

            if root_path is not None:
                self.root_path = root_path
            if auth_token is not None:
                self.auth_token = auth_token
            if ct0 is not None:
                self.ct0 = ct0
            if max_download_routine is not None:
                self.max_download_routine = max_download_routine

            self._get_logger().info("核心配置已保存")
            return True, ""

        except Exception as e:
            self.root_path = old_root_path
            self.auth_token = old_auth_token
            self.ct0 = old_ct0
            self.max_download_routine = old_max_download_routine
            error_msg = f"保存核心配置失败: {e}"
            self._get_logger().error(error_msg)
            return False, error_msg

    def save_proxy(
        self,
        hostname: str,
        port: int,
        use_proxy: bool,
    ) -> Tuple[bool, str]:
        """
        保存代理配置（原子写入）

        Args:
            hostname: 代理主机名
            port: 代理端口
            use_proxy: 是否使用代理

        Returns:
            (成功标志, 错误消息)
        """
        is_valid, error = check_proxy_values(hostname, port, use_proxy)
        if not is_valid:
            return False, error

        old_hostname = self.proxy_hostname
        old_port = self.proxy_tcp_port
        old_use_proxy = self.use_proxy

        try:
            config = self._read_config()
            config["proxy_hostname"] = hostname
            config["proxy_tcp_port"] = port
            config["use_proxy"] = use_proxy

            self.config_dir.mkdir(parents=True, exist_ok=True)

            if not atomic_write_yaml(self.config_file, config, self._get_logger()):
                return False, "文件写入失败"

            self.proxy_hostname = hostname
            self.proxy_tcp_port = port
            self.use_proxy = use_proxy

            self._get_logger().info(f"代理配置已保存: {hostname}:{port}")
            return True, ""

        except Exception as e:
            self.proxy_hostname = old_hostname
            self.proxy_tcp_port = old_port
            self.use_proxy = old_use_proxy
            error_msg = f"保存代理配置失败: {e}"
            self._get_logger().error(error_msg)
            return False, error_msg

    def save_batch_config(self, batch_size: int) -> Tuple[bool, str]:
        """
        保存批量配置（原子写入）

        Args:
            batch_size: 批量大小

        Returns:
            (成功标志, 错误消息)
        """
        if not (1 <= batch_size <= 50):
            return False, "批量大小必须在 1-50 之间"

        old_batch_size = self.file_batch_size

        try:
            config = self._read_config()
            config["file_batch_size"] = batch_size

            self.config_dir.mkdir(parents=True, exist_ok=True)

            if not atomic_write_yaml(self.config_file, config, self._get_logger()):
                return False, "文件写入失败"

            self.file_batch_size = batch_size
            self._get_logger().info(f"批量配置已保存: {batch_size}")
            return True, ""

        except Exception as e:
            self.file_batch_size = old_batch_size
            error_msg = f"保存批量配置失败: {e}"
            self._get_logger().error(error_msg)
            return False, error_msg

    def save_batch_delay_config(
        self,
        success_min: int,
        success_max: int,
        fail_min: int,
        fail_max: int,
    ) -> Tuple[bool, str]:
        """保存双轨延迟配置到 conf.yaml。

        使用原子写入方式保存成功/失败批次延迟配置，并更新实例属性。

        Args:
            success_min: 成功批次最小延迟（秒）。
            success_max: 成功批次最大延迟（秒）。
            fail_min: 失败批次最小延迟（秒）。
            fail_max: 失败批次最大延迟（秒）。

        Returns:
            元组，包含两个元素：
            - bool: 保存是否成功。
            - str: 错误消息（成功时为空字符串）。

        Example:
            >>> config = TMDConfig()
            >>> success, error = config.save_batch_delay_config(1, 5, 10, 30)
            >>> if success:
            ...     print("延迟配置已保存")
        """
        if not yaml:
            return False, "yaml 模块未安装"

        # 规范化参数
        s_min, s_max = max(0, int(success_min)), max(0, int(success_max))
        f_min, f_max = max(0, int(fail_min)), max(0, int(fail_max))

        # 确保 min <= max
        if s_min > s_max:
            s_min, s_max = s_max, s_min
        if f_min > f_max:
            f_min, f_max = f_max, f_min

        # 保存旧值用于回滚
        old_values = (
            self.batch_delay_success_min,
            self.batch_delay_success_max,
            self.batch_delay_fail_min,
            self.batch_delay_fail_max,
        )

        try:
            # 读取现有配置
            config = self._read_config()

            # 设置延迟配置
            config["batch_delay"] = {
                "success": {"min": s_min, "max": s_max},
                "fail": {"min": f_min, "max": f_max},
            }

            # 确保目录存在
            self.config_dir.mkdir(parents=True, exist_ok=True)

            # 原子写入
            if not atomic_write_yaml(self.config_file, config, self._get_logger()):
                return False, "文件写入失败"

            # 更新实例属性
            self.batch_delay_success_min = s_min
            self.batch_delay_success_max = s_max
            self.batch_delay_fail_min = f_min
            self.batch_delay_fail_max = f_max

            # 记录日志
            if s_max > 0:
                self._get_logger().info(f"成功延迟已启用: {s_min}-{s_max}秒")
            if f_max > 0:
                self._get_logger().info(f"失败延迟已启用: {f_min}-{f_max}秒")
            if s_max == 0 and f_max == 0:
                self._get_logger().info("批次延迟保护已禁用")

            return True, ""

        except Exception as e:
            # 回滚
            (
                self.batch_delay_success_min,
                self.batch_delay_success_max,
                self.batch_delay_fail_min,
                self.batch_delay_fail_max,
            ) = old_values
            error_msg = f"保存延迟配置失败: {e}"
            self._get_logger().error(error_msg)
            return False, str(e)

    def save_quick_list_interval(self, interval: int) -> Tuple[bool, str]:
        """保存快速列表间隔。

        保存列表间间隔配置（0-300秒），使用 _save_config_field 方法实现。

        Args:
            interval: 列表间间隔（秒），范围 0-300。

        Returns:
            元组，包含两个元素：
            - bool: 保存是否成功。
            - str: 错误消息（成功时为空字符串）。

        Example:
            >>> config = TMDConfig()
            >>> success, error = config.save_quick_list_interval(30)
            >>> if success:
            ...     print(f"间隔已设置为 {config.quick_list_interval} 秒")
        """
        if not (0 <= interval <= 300):
            return False, "间隔必须在 0-300 秒之间"

        old_interval = self.quick_list_interval

        success, error = self._save_config_field(
            field_path="quick_list_interval",
            new_value=interval,
            log_msg=f"列表下载间隔已更新: {interval}秒",
        )

        if success:
            self.quick_list_interval = interval
        else:
            self.quick_list_interval = old_interval

        return success, error


__all__ = ["TMDConfig"]
