# -*- coding: utf-8 -*-
"""
Cookie 服务模块

提供备用账号 Cookie 的数据管理功能。

注意：UI 交互逻辑已迁移至 menus/cookie_menu.py

主要功能：
- 加载/保存备用账号 Cookie
- 添加/删除 Cookie
- 启用/禁用账号
- 解析 Cookie 字符串
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

try:
    import yaml
except ImportError:
    yaml = None

from ..constants import Constants
from ..tmd_types import IConfig, ICookieService, ILogger, OperationResult
from ..utils.file_io import atomic_write_yaml
from ..utils.formatters import mask_token
from ..utils.patterns import COOKIE_AUTH_TOKEN_RE, COOKIE_CT0_RE


class CookieService(ICookieService):
    """Cookie 服务。

    提供备用账号 Cookie 管理功能，支持轮询下载以突破限速。

    Attributes:
        config: 配置实例
        logger: 日志实例

    Example:
        >>> from tmdc.services.cookie_service import CookieService
        >>> service = CookieService(config, logger)
        >>> cookies = service.load_additional_cookies()
        >>> service.add_cookie("token123", "ct0456")
    """

    def __init__(self, config: IConfig, logger: ILogger) -> None:
        """初始化 Cookie 服务。

        Args:
            config: 配置实例
            logger: 日志实例
        """
        self.config = config
        self.logger = logger

    def load_cookies(self) -> List[Dict[str, str]]:
        """加载 Cookie 列表。"""
        return self.load_additional_cookies()

    def save_cookies(self, cookies: List[Dict[str, str]]) -> Tuple[bool, str]:
        """保存 Cookie 列表。"""
        return self.save_additional_cookies(cookies)

    def load_additional_cookies(self) -> List[Dict[str, str]]:
        """从 YAML 文件读取备用账号列表。

        Returns:
            Cookie 字典列表，每个字典包含 auth_token 和 ct0
        """
        if not yaml:
            return []

        disabled_file = self.config.cookie_file.with_suffix(".yaml.disabled")
        target_file = None

        if self.config.cookie_file.exists():
            target_file = self.config.cookie_file
        elif disabled_file.exists():
            target_file = disabled_file

        if not target_file or not target_file.exists():
            return []

        try:
            with open(target_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if isinstance(data, list):
                    valid_cookies = []
                    for item in data:
                        if isinstance(item, dict) and item.get("auth_token") and item.get("ct0"):
                            valid_cookies.append(item)
                    return valid_cookies
                return []
        except Exception as e:
            self.logger.warning(f"读取备用账号失败: {e}")
            return []

    def save_additional_cookies(self, cookies: List[Dict[str, str]]) -> Tuple[bool, str]:
        """事务性保存 Cookie 列表。

        Args:
            cookies: Cookie 字典列表

        Returns:
            (成功标志, 错误消息)
        """
        if not yaml:
            return False, "未安装 PyYAML"

        disabled_file = self.config.cookie_file.with_suffix(".yaml.disabled")

        was_disabled = False
        if disabled_file.exists() and not self.config.cookie_file.exists():
            was_disabled = True
            try:
                disabled_file.replace(self.config.cookie_file)
                self.logger.info("检测到禁用状态，保存操作将自动启用账号")
            except Exception as e:
                return False, f"无法从禁用状态恢复: {e}"

        backup_data = None
        if self.config.cookie_file.exists():
            try:
                with open(self.config.cookie_file, "r", encoding="utf-8") as f:
                    backup_data = f.read()
            except Exception:
                pass

        try:
            if atomic_write_yaml(self.config.cookie_file, cookies, self.logger):
                self.logger.info(f"保存备用账号成功，当前共 {len(cookies)} 个")
                return True, ""
            else:
                raise IOError("原子写入返回失败")
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"保存备用账号失败: {error_msg}")

            if backup_data is not None:
                try:
                    with open(self.config.cookie_file, "w", encoding="utf-8") as f:
                        f.write(backup_data)
                    self.logger.info("已恢复原文件内容")
                except Exception as restore_err:
                    self.logger.error(f"恢复文件失败: {restore_err}")

            if was_disabled and self.config.cookie_file.exists():
                try:
                    self.config.cookie_file.replace(disabled_file)
                except Exception:
                    pass

            return False, error_msg

    def toggle_cookies_disabled(self) -> OperationResult:
        """切换备用账号的启用/禁用状态（纯业务逻辑，无 UI 输出）

        Returns:
            OperationResult: 操作结果
        """
        disabled_file = self.config.cookie_file.with_suffix(".yaml.disabled")

        try:
            if self.config.cookie_file.exists():
                self.config.cookie_file.replace(disabled_file)
                self.logger.info("备用账号已暂时禁用")
                return OperationResult(
                    success=True,
                    message=f"已暂时禁用备用账号\n账号数据已保存至: {disabled_file.name}\n下载时将不再使用备用账号轮询",
                    data={"action": "disabled"}
                )

            elif disabled_file.exists():
                disabled_file.replace(self.config.cookie_file)
                count = len(self.load_additional_cookies())
                self.logger.info(f"备用账号已启用，共 {count} 个")
                return OperationResult(
                    success=True,
                    message=f"已恢复启用备用账号\n当前共有 {count} 个备用账号可用于轮询",
                    data={"action": "enabled", "count": count}
                )

            else:
                return OperationResult(
                    success=False,
                    error="没有可启用或禁用的备用账号（文件不存在）"
                )

        except PermissionError:
            error_msg = "文件被占用或无权限，操作失败"
            self.logger.error(error_msg)
            return OperationResult(success=False, error=error_msg)
        except Exception as e:
            error_msg = f"操作失败: {e}"
            self.logger.error(error_msg)
            return OperationResult(success=False, error=error_msg)

    def add_cookie(self, auth_token: str, ct0: str) -> Tuple[bool, str]:
        """添加新 Cookie。

        Args:
            auth_token: auth_token 值
            ct0: ct0 值

        Returns:
            Tuple[bool, str]: (是否成功, 错误信息)
        """
        cookies = self.load_additional_cookies()

        for cookie in cookies:
            if cookie.get("auth_token") == auth_token:
                return False, "该账号已存在（auth_token 重复）"
            if cookie.get("ct0") == ct0:
                return False, "该账号已存在（ct0 重复）"

        cookies.append({"auth_token": auth_token, "ct0": ct0})

        return self.save_additional_cookies(cookies)

    def remove_cookie(self, index: int) -> Tuple[bool, str, Optional[Dict[str, str]]]:
        """删除指定索引的 Cookie。

        Args:
            index: Cookie 索引（从 0 开始）

        Returns:
            Tuple[bool, str, Optional[Dict]]: (是否成功, 错误信息, 被删除的 Cookie)
        """
        cookies = self.load_additional_cookies()

        if not (0 <= index < len(cookies)):
            return False, "索引超出范围", None

        removed = cookies.pop(index)
        success, error = self.save_additional_cookies(cookies)

        if success:
            self.logger.info(f"已删除备用账号: {mask_token(removed.get('auth_token', ''))}")
            return True, "", removed
        else:
            return False, error, None

__all__ = ["CookieService"]
