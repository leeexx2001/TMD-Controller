# -*- coding: utf-8 -*-
"""
TMD 类型定义模块

定义 Protocol 接口和数据类，实现依赖反转和类型安全。

本模块包含：
- Protocol 接口定义：用于依赖注入和类型检查
- 数据类定义：用于数据传输和存储
- 类型别名：简化复杂类型的使用
"""

from __future__ import annotations

# 标准库
import logging
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Generator,
    List,
    Optional,
    Protocol,
    Tuple,
    TypeVar,
    Union,
    runtime_checkable,
)

if TYPE_CHECKING:
    import sqlite3

# 第三方库（无）

# 本地模块（无 - 本模块是基础类型定义模块）


# ==================== 类型别名 ====================

CookieDict = Dict[str, str]
"""Cookie 字典类型别名"""


# ==================== Protocol 接口定义 ====================


@runtime_checkable
class ILogger(Protocol):
    """
    日志接口

    定义日志记录的标准接口，支持结构化日志记录。

    Example:
        >>> class ConsoleLogger:
        ...     def info(self, msg: str) -> None: print(f"[INFO] {msg}")
        ...     def warning(self, msg: str) -> None: print(f"[WARN] {msg}")
        ...     def error(self, msg: str) -> None: print(f"[ERROR] {msg}")
        ...     def debug(self, msg: str) -> None: print(f"[DEBUG] {msg}")
    """

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """记录 INFO 级别日志"""
        ...

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """记录 WARNING 级别日志"""
        ...

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """记录 ERROR 级别日志"""
        ...

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """记录 DEBUG 级别日志"""
        ...

    def critical(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """记录 CRITICAL 级别日志"""
        ...


@runtime_checkable
class IConfig(Protocol):
    """
    配置接口

    定义配置管理的标准接口，包含所有配置属性和操作方法。

    Attributes:
        auth_token: Twitter auth_token
        ct0: Twitter CSRF token
        root_path: TMD 下载根目录
        use_proxy: 是否使用代理
        proxy_hostname: 代理主机名
        proxy_tcp_port: 代理端口
        file_batch_size: 文件分批大小
        max_download_routine: 最大并行下载数
        quick_list_ids: 快速列表 ID 列表
        quick_list_interval: 列表间间隔（秒）
        config_file: 配置文件路径
        config_dir: 配置目录路径
        db_path: 数据库路径（可选）
        cookie_file: Cookie 文件路径
    """

    # 核心配置属性
    auth_token: Optional[str]
    ct0: Optional[str]
    root_path: Optional[str]
    use_proxy: bool
    proxy_hostname: str
    proxy_tcp_port: int
    file_batch_size: int
    max_download_routine: int
    quick_list_ids: List[str]
    quick_list_interval: int

    # 路径属性
    config_file: Path
    config_dir: Path
    cookie_file: Path

    # 延迟配置属性
    batch_delay_success_min: int
    batch_delay_success_max: int
    batch_delay_fail_min: int
    batch_delay_fail_max: int

    @property
    def db_path(self) -> Optional[Path]:
        """获取数据库路径"""
        ...

    def save_core_config(
        self,
        root_path: Optional[str] = None,
        auth_token: Optional[str] = None,
        ct0: Optional[str] = None,
        max_download_routine: Optional[int] = None,
        allow_partial: bool = False,
    ) -> Tuple[bool, str]:
        """
        保存核心配置

        Args:
            root_path: TMD 下载根目录
            auth_token: Twitter auth_token
            ct0: Twitter CSRF token
            max_download_routine: 最大并行下载数
            allow_partial: 是否允许部分保存

        Returns:
            (成功标志, 错误消息)
        """
        ...

    def save_proxy(
        self,
        hostname: str,
        port: int,
        use_proxy: bool,
    ) -> Tuple[bool, str]:
        """
        保存代理配置

        Args:
            hostname: 代理主机名
            port: 代理端口
            use_proxy: 是否使用代理

        Returns:
            (成功标志, 错误消息)
        """
        ...

    def save_batch_config(self, batch_size: int) -> Tuple[bool, str]:
        """
        保存批量配置

        Args:
            batch_size: 批量大小

        Returns:
            (成功标志, 错误消息)
        """
        ...

    def save_quick_list_ids(self, list_ids: Optional[List[str]] = None) -> Tuple[bool, str]:
        """
        保存快速列表 ID

        Args:
            list_ids: 列表 ID 列表

        Returns:
            (成功标志, 错误消息)
        """
        ...

    def save_batch_delay_config(
        self,
        success_min: int,
        success_max: int,
        fail_min: int,
        fail_max: int,
    ) -> Tuple[bool, str]:
        """
        保存双轨延迟配置

        Args:
            success_min: 成功延迟最小值
            success_max: 成功延迟最大值
            fail_min: 失败延迟最小值
            fail_max: 失败延迟最大值

        Returns:
            (成功标志, 错误消息)
        """
        ...

    def save_quick_list_interval(self, interval: int) -> Tuple[bool, str]:
        """
        保存快速列表间隔

        Args:
            interval: 间隔秒数

        Returns:
            (成功标志, 错误消息)
        """
        ...

    @property
    def default_quick_list_id(self) -> Optional[str]:
        """获取默认快速列表 ID"""
        ...

    @property
    def is_batch_delay_success_enabled(self) -> bool:
        """检查成功延迟是否启用"""
        ...

    @property
    def is_batch_delay_fail_enabled(self) -> bool:
        """检查失败延迟是否启用"""
        ...


@runtime_checkable
class IUIHelper(Protocol):
    """
    UI 辅助接口

    定义用户界面交互的标准接口。

    Example:
        >>> class ConsoleUI:
        ...     def clear_screen(self) -> None: os.system('cls')
        ...     def pause(self) -> None: input("按回车继续...")
    """

    def clear_screen(self) -> None:
        """清空屏幕"""
        ...

    def pause(self, prompt: str = "按回车键继续...") -> None:
        """
        暂停等待用户输入

        Args:
            prompt: 提示消息
        """
        ...

    def safe_input(
        self,
        prompt: str,
        *,
        allow_empty: bool = False,
        default: Optional[str] = None,
    ) -> Optional[str]:
        """
        安全输入方法

        Args:
            prompt: 输入提示
            allow_empty: 是否允许空输入
            default: 默认值

        Returns:
            用户输入的字符串，如果输入无效则返回 None
        """
        ...

    def show_header(self, title: str, subtitle: Optional[str] = None) -> None:
        """
        显示标题头

        Args:
            title: 主标题
            subtitle: 副标题（可选）
        """
        ...

    def confirm_action(
        self,
        prompt: str,
        *,
        explicit: bool = False,
        default: bool = False,
        logger: Optional[ILogger] = None,
    ) -> bool:
        """
        确认操作

        Args:
            prompt: 确认提示
            explicit: 是否需要显式确认（输入 yes/no）
            default: 默认值
            logger: 日志实例（可选）

        Returns:
            用户是否确认
        """
        ...

    def print_success(self, msg: str) -> None:
        """打印成功消息"""
        ...

    def print_error(self, msg: str) -> None:
        """打印错误消息"""
        ...

    def print_warning(self, msg: str) -> None:
        """打印警告消息"""
        ...

    def print_info(self, msg: str) -> None:
        """打印信息消息"""
        ...

    def print_separator(self) -> None:
        """打印分隔线"""
        ...

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

        Args:
            prompt: 输入提示
            min_val: 最小值
            max_val: 最大值
            default: 默认值

        Returns:
            用户输入的数字，如果无效则返回 None
        """
        ...

    def flush_keyboard_buffer(self) -> None:
        """清空键盘缓冲区"""
        ...

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
        """
        ...

    def show_batch_summary(
        self,
        total: int,
        success: int,
        failed: int,
        failed_items: Optional[List[str]] = None,
    ) -> None:
        """
        显示批量操作摘要

        Args:
            total: 总数
            success: 成功数
            failed: 失败数
            failed_items: 失败项目列表（可选）
        """
        ...


@runtime_checkable
class IDownloadService(Protocol):
    """
    下载服务接口（纯业务逻辑，无 UI 依赖）

    定义下载操作的标准接口。

    Attributes:
        config: 配置实例
        logger: 日志实例
    """

    config: IConfig
    logger: ILogger

    def download_user(
        self,
        username: str,
        *,
        timestamp: Optional[datetime] = None,
        source: str = "",
    ) -> "DownloadResult":
        """
        下载用户媒体

        Args:
            username: Twitter 用户名
            timestamp: 时间戳过滤（可选）
            source: 来源描述（可选）

        Returns:
            DownloadResult: 下载结果
        """
        ...

    def download_list(
        self,
        list_id: str,
        *,
        timestamp: Optional[datetime] = None,
    ) -> "DownloadResult":
        """
        下载列表媒体

        Args:
            list_id: Twitter 列表 ID
            timestamp: 时间戳过滤（可选）

        Returns:
            DownloadResult: 下载结果
        """
        ...

    def download_batch(
        self,
        users: Optional[List[str]] = None,
        lists: Optional[List[str]] = None,
    ) -> "DownloadResult":
        """
        批量下载用户和列表（单次 TMD 调用）

        Args:
            users: 用户名列表
            lists: 列表 ID 列表

        Returns:
            DownloadResult: 下载结果
        """
        ...

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
        ...

    def check_list_exists(self, list_id: str) -> bool:
        """
        检查列表是否存在

        Args:
            list_id: 列表 ID

        Returns:
            列表存在返回 True
        """
        ...

    def check_pending_tweets(self, root_path: Optional[str]) -> Optional[int]:
        """
        检查待处理推文数量

        Args:
            root_path: 下载根目录

        Returns:
            待处理推文数量
        """
        ...


@runtime_checkable
class IDatabaseService(Protocol):
    """
    数据库服务接口

    定义数据库操作的标准接口。
    """

    @contextmanager
    def db_session(
        self,
    ) -> Generator[Optional["sqlite3.Cursor"], None, None]:
        """
        数据库连接上下文管理器（公共接口）

        自动管理连接的创建、提交、回滚和关闭。

        Yields:
            sqlite3.Cursor: 数据库游标，如果连接失败则 yield None
        """
        ...

    def find_users(
        self,
        keyword: str,
        *,
        limit: Optional[int] = None,
        default_limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        搜索用户

        Args:
            keyword: 搜索关键词
            limit: 返回结果数量限制（默认使用 default_limit）
            default_limit: 默认限制数量（当 limit 为 None 时使用）

        Returns:
            用户信息列表
        """
        ...

    def find_unlinked_users(
        self,
        *,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        查询未关联列表的用户

        查询存在于 users 表但在 user_links 表中没有关联记录的用户。

        Args:
            limit: 返回结果数量限制（None 表示不限制）

        Returns:
            未关联用户列表，包含以下字段：
            - id: 用户 ID
            - screen_name: 用户名
            - name: 显示名称
            - entity_id: 用户实体 ID（可能为 None）
            - is_accessible: 是否可访问（0=不可访问，1=可访问）
        """
        ...

    def check_list_metadata_exists(self, list_id: int) -> bool:
        """
        检查列表元数据是否存在（lsts 表）

        Args:
            list_id: 列表 ID

        Returns:
            列表是否存在
        """
        ...

    def check_list_entity_exists(self, list_id: int) -> bool:
        """
        检查列表实体是否存在（lst_entities 表）

        Args:
            list_id: 列表 ID

        Returns:
            列表实体是否存在
        """
        ...

    def get_user_entity_info(self, screen_name: str) -> Optional[Dict[str, Any]]:
        """
        获取用户实体信息

        Args:
            screen_name: 用户名

        Returns:
            用户信息字典，包含 id, screen_name, name, entity_id, latest_release_time
        """
        ...

    def get_entity_by_id(self, entity_id: int) -> Optional[Dict[str, Any]]:
        """
        通过实体 ID 获取实体信息

        Args:
            entity_id: 用户实体 ID

        Returns:
            实体信息字典，包含 screen_name, entity_id
        """
        ...

    def set_user_timestamp(
        self,
        entity_id: int,
        target_date: Optional[datetime],
    ) -> Tuple[bool, Optional[str]]:
        """
        直接设置用户时间戳

        Args:
            entity_id: 用户实体 ID
            target_date: 目标时间戳，None 表示重置为全量下载

        Returns:
            (是否成功, screen_name) - 成功时返回用户名，失败时返回 None
        """
        ...

    def set_list_timestamp(
        self,
        list_id: int,
        target_date: Optional[datetime],
    ) -> bool:
        """
        直接设置列表时间戳

        Args:
            list_id: 列表 ID
            target_date: 目标时间戳，None 表示重置为全量下载

        Returns:
            是否成功
        """
        ...

    def get_path_statistics(self, path: str) -> Dict[str, Any]:
        """
        获取路径统计信息

        Args:
            path: 路径

        Returns:
            统计信息字典
        """
        ...

    def execute_transaction(self, operations: List[Tuple[str, tuple]]) -> bool:
        """
        执行事务操作

        Args:
            operations: 操作列表，每个操作是 (SQL, params) 元组

        Returns:
            操作是否成功
        """
        ...

    def delete_user_project(
        self,
        uid: int,
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """删除用户项目的所有数据库记录

        级联删除 user_links、user_entities、user_previous_names、users 表中
        与指定用户 ID 相关的所有记录。

        Args:
            uid: 用户 ID（Twitter 用户唯一标识符）

        Returns:
            Tuple[是否成功, 消息/错误信息, 各表删除统计字典]
            统计字典格式: {"links": n, "entities": n, "names": n, "users": n}
        """
        ...


@runtime_checkable
class IProxyService(Protocol):
    """
    代理服务接口

    定义代理操作的标准接口。
    """

    config: IConfig
    logger: ILogger

    def check_proxy_reachable(
        self,
        timeout: Optional[float] = None,
        use_cache: bool = True,
    ) -> bool:
        """
        检查代理是否可达

        Args:
            timeout: 超时时间（秒），默认使用 Constants.PROXY_TIMEOUT
            use_cache: 是否使用缓存

        Returns:
            代理是否可达
        """
        ...

    def save_proxy_config(
        self,
        hostname: Optional[str] = None,
        port: Optional[int] = None,
        use_proxy: Optional[bool] = None,
    ) -> Tuple[bool, str]:
        """
        保存代理配置到 conf.yaml

        Args:
            hostname: 代理主机名（None 保持原值）
            port: 代理端口（None 保持原值）
            use_proxy: 是否使用代理（None 保持原值）

        Returns:
            (成功标志, 错误消息)
        """
        ...

    def get_status(self) -> "ProxyStatus":
        """
        获取代理状态

        Returns:
            代理状态信息
        """
        ...


@runtime_checkable
class ICookieService(Protocol):
    """
    Cookie 服务接口

    定义 Cookie 操作的标准接口。
    """

    config: IConfig
    logger: ILogger

    def load_additional_cookies(self) -> List[Dict[str, str]]:
        """
        从 YAML 文件读取备用账号列表

        Returns:
            Cookie 字典列表
        """
        ...

    def save_additional_cookies(self, cookies: List[Dict[str, str]]) -> Tuple[bool, str]:
        """
        事务性保存 Cookie 列表

        Args:
            cookies: Cookie 字典列表

        Returns:
            (成功标志, 错误消息)
        """
        ...

    def add_cookie(self, auth_token: str, ct0: str) -> Tuple[bool, str]:
        """
        添加新 Cookie

        Args:
            auth_token: auth_token 值
            ct0: ct0 值

        Returns:
            (成功标志, 错误消息)
        """
        ...

    def remove_cookie(self, index: int) -> Tuple[bool, str, Optional[Dict[str, str]]]:
        """
        删除指定索引的 Cookie

        Args:
            index: Cookie 索引（从 0 开始）

        Returns:
            (是否成功, 错误信息, 被删除的 Cookie)
        """
        ...

    def toggle_cookies_disabled(self) -> "OperationResult":
        """切换备用账号的启用/禁用状态

        Returns:
            OperationResult: 操作结果
                - success: 是否成功
                - message: 状态消息
                - error: 错误信息
                - data: {"action": "enabled"|"disabled", "count": int}
        """
        ...

    # 注意：parse_cookie_string 已移除
    # 该功能已迁移到 tmdc.utils.validators.parse_cookie_string()


@runtime_checkable
class IProgressCallback(Protocol):
    """
    进度回调接口

    用于长时间运行操作的进度报告。
    实现此接口的服务不直接产生 UI 输出。
    """

    def on_start(self, total: int, message: str) -> None:
        """操作开始

        Args:
            total: 总任务数
            message: 开始消息
        """
        ...

    def on_progress(self, current: int, message: str) -> None:
        """进度更新

        Args:
            current: 当前进度
            message: 进度消息
        """
        ...

    def on_item_success(self, item_id: str, message: str) -> None:
        """项目成功

        Args:
            item_id: 项目标识
            message: 成功消息
        """
        ...

    def on_item_failed(self, item_id: str, error: str) -> None:
        """项目失败

        Args:
            item_id: 项目标识
            error: 错误消息
        """
        ...

    def on_complete(self, success_count: int, fail_count: int) -> None:
        """操作完成

        Args:
            success_count: 成功数量
            fail_count: 失败数量
        """
        ...

    def is_cancelled(self) -> bool:
        """检查是否已取消"""
        ...


@runtime_checkable
class IRemedyService(Protocol):
    """
    补救服务接口

    定义补救下载操作的标准接口。
    """

    config: IConfig
    logger: ILogger
    ui: IUIHelper

    def execute(self) -> bool:
        """
        执行补救下载

        Returns:
            操作是否成功
        """
        ...

    def get_failed_tasks(self) -> List[Dict[str, Any]]:
        """
        获取失败任务列表

        Returns:
            失败任务信息列表
        """
        ...


@runtime_checkable
class ITimestampService(Protocol):
    """时间戳服务接口

    定义时间戳操作的标准接口。
    """

    config: IConfig
    logger: ILogger
    database_service: "IDatabaseService"
    download_service: Optional["IDownloadService"]

    def set_sync_timestamp(
        self,
        entity_id: int,
        target_date: Optional[datetime],
    ) -> "OperationResult":
        """设置同步时间戳

        Args:
            entity_id: 实体 ID
            target_date: 目标日期（None 表示清除）

        Returns:
            OperationResult: 操作结果
        """
        ...

    def batch_set_list_timestamp(
        self,
        list_id: int,
        target_date: Optional[datetime],
    ) -> "BatchOperationResult":
        """批量设置列表中所有用户的时间戳

        Args:
            list_id: 列表 ID
            target_date: 目标日期

        Returns:
            BatchOperationResult: 批量操作结果
        """
        ...

    def get_or_create_user_entity(
        self,
        screen_name: str,
        target_date: Optional[datetime] = None,
    ) -> "OperationResult":
        """获取或创建用户实体

        Args:
            screen_name: 用户屏幕名
            target_date: 目标日期（可选）

        Returns:
            OperationResult: 操作结果，data 包含 entity_id
        """
        ...

    def get_or_create_list_entity(
        self,
        list_id: int,
        target_date: Optional[datetime] = None,
    ) -> "OperationResult":
        """获取或创建列表实体

        Args:
            list_id: 列表 ID
            target_date: 目标日期（可选）

        Returns:
            OperationResult: 操作结果，data 包含 entity_id
        """
        ...


@runtime_checkable
class IInputParser(Protocol):
    """
    输入解析器接口

    定义输入解析的标准接口。
    """

    def parse_user_input(self, input_str: str) -> List[str]:
        """
        解析用户输入

        Args:
            input_str: 输入字符串

        Returns:
            用户名列表
        """
        ...

    def parse_list_input(self, input_str: str) -> List[str]:
        """
        解析列表输入

        Args:
            input_str: 输入字符串

        Returns:
            列表 ID 列表
        """
        ...


# ==================== 数据类定义 ====================


@dataclass
class OperationResult:
    """通用操作结果数据类

    用于服务层返回操作结果，由调用方（菜单/CLI）负责显示。

    Attributes:
        success: 操作是否成功
        message: 成功消息
        error: 错误消息
        code: 状态码
        data: 附加数据

    Example:
        >>> result = OperationResult(success=True, message="操作成功")
        >>> if result.success:
        ...     print(result.message)
    """

    success: bool
    message: str = ""
    error: str = ""
    code: str = ""
    data: Optional[Dict[str, Any]] = None


@dataclass
class BatchOperationResult(OperationResult):
    """批量操作结果数据类

    继承 OperationResult，添加批量操作的统计信息。

    Attributes:
        total: 总数量
        success_count: 成功数量
        failed_count: 失败数量
        failed_items: 失败项目列表

    Example:
        >>> result = BatchOperationResult(
        ...     success=True,
        ...     total=10,
        ...     success_count=8,
        ...     failed_count=2,
        ...     failed_items=["user1", "user2"]
        ... )
    """

    total: int = 0
    success_count: int = 0
    failed_count: int = 0
    failed_items: List[str] = field(default_factory=list)


@dataclass
class DownloadResult:
    """
    下载结果数据类

    存储下载操作的完整结果信息。

    Attributes:
        exit_code: 退出码（0 表示成功）
        warn_count: 警告数量
        error_count: 错误数量
        warn_users: 警告用户列表
        error_messages: 错误消息列表
        raw_output: 原始输出内容
        duration: 下载耗时（秒）
        target_type: 目标类型 ("user" | "list" | "following" | "profile")
        target_id: 目标ID（用户名或列表ID）
        log_desc: 日志描述
        success: 是否成功
    """

    exit_code: int = 0
    warn_count: int = 0
    error_count: int = 0
    warn_users: List[str] = field(default_factory=list)
    error_messages: List[str] = field(default_factory=list)
    raw_output: str = ""
    duration: float = 0.0
    target_type: str = ""
    target_id: str = ""
    log_desc: str = ""

    @property
    def success(self) -> bool:
        """检查下载是否成功"""
        return self.exit_code == 0 and self.error_count == 0

    @property
    def has_warnings(self) -> bool:
        """检查是否有警告"""
        return self.warn_count > 0

    @property
    def has_errors(self) -> bool:
        """检查是否有错误"""
        return self.error_count > 0 or self.exit_code != 0

    def get_success_message(self) -> str:
        """获取成功消息"""
        if self.target_type == "user":
            return f"✅ 用户 @{self.target_id} 下载完成"
        elif self.target_type == "list":
            return f"✅ 列表 {self.target_id} 下载完成"
        elif self.target_type == "following":
            return f"✅ @{self.target_id} 关注列表下载完成"
        elif self.target_type == "profile":
            return f"✅ @{self.target_id} Profile 下载完成"
        return "✅ 任务完成"

    def get_error_message(self) -> str:
        """获取错误消息"""
        if self.target_type == "user":
            return f"❌ 用户 @{self.target_id} 下载失败"
        elif self.target_type == "list":
            return f"❌ 列表 {self.target_id} 下载失败"
        return "❌ 任务失败"

    def get_start_message(self) -> str:
        """获取开始消息"""
        if self.target_type == "user":
            return f"📝 开始下载用户: @{self.target_id}"
        elif self.target_type == "list":
            return f"📝 开始下载列表: {self.target_id}"
        elif self.target_type == "following":
            return f"📝 开始下载 @{self.target_id} 的关注列表"
        elif self.target_type == "profile":
            return f"📝 开始下载 Profile: @{self.target_id}"
        return "📝 开始执行任务"

    def merge(self, other: "DownloadResult") -> "DownloadResult":
        """
        合并另一个结果

        Args:
            other: 另一个下载结果

        Returns:
            合并后的结果
        """
        return DownloadResult(
            exit_code=self.exit_code if self.exit_code != 0 else other.exit_code,
            warn_count=self.warn_count + other.warn_count,
            error_count=self.error_count + other.error_count,
            warn_users=list(set(self.warn_users + other.warn_users)),
            error_messages=self.error_messages + other.error_messages,
            raw_output=self.raw_output + other.raw_output,
            duration=self.duration + other.duration,
        )


@dataclass
class UserInfo:
    """
    用户信息数据类

    存储用户的完整信息。

    Attributes:
        screen_name: 用户屏幕名（@后面的名字）
        name: 用户显示名称
        entity_id: 数据库实体 ID（可选）
        latest_release_time: 最新发布时间（可选）
        timestamp: 时间戳（可选）
    """

    screen_name: str
    name: str
    entity_id: Optional[int] = None
    latest_release_time: Optional[str] = None
    timestamp: Optional[datetime] = None

    def __str__(self) -> str:
        """返回用户信息的字符串表示"""
        parts = [f"@{self.screen_name}"]
        if self.name:
            parts.append(f"({self.name})")
        if self.timestamp:
            parts.append(f"[{self.timestamp.strftime('%Y-%m-%d')}]")
        return " ".join(parts)


@dataclass
class ListInfo:
    """
    列表信息数据类

    存储列表的完整信息。

    Attributes:
        list_id: 列表 ID
        name: 列表名称（可选）
        member_count: 成员数量
        timestamp: 时间戳（可选）
    """

    list_id: int
    name: Optional[str] = None
    member_count: int = 0
    timestamp: Optional[datetime] = None

    def __str__(self) -> str:
        """返回列表信息的字符串表示"""
        parts = [f"列表 {self.list_id}"]
        if self.name:
            parts.append(f"({self.name})")
        if self.member_count > 0:
            parts.append(f"[{self.member_count} 成员]")
        return " ".join(parts)


@dataclass
class ProxyStatus:
    """
    代理状态数据类

    存储代理的当前状态信息。

    Attributes:
        is_enabled: 是否启用代理
        is_reachable: 代理是否可达
        hostname: 代理主机名
        port: 代理端口
        last_check_time: 上次检查时间
        error_message: 错误消息（如果有）
    """

    is_enabled: bool
    is_reachable: bool = False
    hostname: str = "127.0.0.1"
    port: int = 7897
    last_check_time: Optional[datetime] = None
    error_message: Optional[str] = None

    @property
    def address(self) -> str:
        """获取代理地址"""
        return f"{self.hostname}:{self.port}"

    @property
    def status_text(self) -> str:
        """获取状态文本"""
        if not self.is_enabled:
            return "已禁用"
        if self.is_reachable:
            return "可用"
        return f"不可用: {self.error_message or '未知错误'}"


@dataclass
class CookieInfo:
    """
    Cookie 信息数据类

    存储单个 Cookie 的信息。

    Attributes:
        name: Cookie 名称
        value: Cookie 值
        domain: Cookie 域名（可选）
        path: Cookie 路径（可选）
    """

    name: str
    value: str
    domain: Optional[str] = None
    path: Optional[str] = "/"

    @property
    def is_masked(self) -> bool:
        """检查值是否已脱敏"""
        return "***" in self.value

    def mask_value(self, visible_chars: int = 4) -> str:
        """
        脱敏 Cookie 值

        Args:
            visible_chars: 可见字符数

        Returns:
            脱敏后的值
        """
        if len(self.value) <= visible_chars:
            return "*" * len(self.value)
        return self.value[:visible_chars] + "***"


@dataclass
class BatchConfig:
    """
    批量配置数据类

    存储批量下载的配置信息。

    Attributes:
        batch_size: 批量大小
        delay_success_min: 成功延迟最小值（秒）
        delay_success_max: 成功延迟最大值（秒）
        delay_fail_min: 失败延迟最小值（秒）
        delay_fail_max: 失败延迟最大值（秒）
    """

    batch_size: int = 3
    delay_success_min: int = 0
    delay_success_max: int = 0
    delay_fail_min: int = 0
    delay_fail_max: int = 0

    @property
    def is_delay_success_enabled(self) -> bool:
        """检查成功延迟是否启用"""
        return self.delay_success_max > 0

    @property
    def is_delay_fail_enabled(self) -> bool:
        """检查失败延迟是否启用"""
        return self.delay_fail_max > 0


@dataclass
class MenuOption:
    """
    菜单选项数据类

    存储菜单选项的信息。

    Attributes:
        key: 选项键
        name: 选项名称
        description: 选项描述
        handler: 选项处理函数
    """

    key: str
    name: str
    description: str = ""
    handler: Optional[Callable[[], None]] = None


# ==================== 泛型类型变量 ====================

T = TypeVar("T")
"""通用类型变量"""

TConfig = TypeVar("TConfig", bound=IConfig)
"""配置类型变量"""

TService = TypeVar("TService")
"""服务类型变量"""


# ==================== 工具函数 ====================


def create_logger(name: str = "TMDController") -> logging.Logger:
    """
    创建日志记录器

    Args:
        name: 日志记录器名称

    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


__all__ = [
    # 类型别名
    "CookieDict",
    # Protocol 接口
    "ILogger",
    "IConfig",
    "IUIHelper",
    "IDownloadService",
    "IDatabaseService",
    "IProxyService",
    "ICookieService",
    "IRemedyService",
    "ITimestampService",
    "IInputParser",
    "IProgressCallback",
    # 数据类
    "OperationResult",
    "BatchOperationResult",
    "DownloadResult",
    "UserInfo",
    "ListInfo",
    "ProxyStatus",
    "CookieInfo",
    "BatchConfig",
    "MenuOption",
    # 类型变量
    "T",
    "TConfig",
    "TService",
    # 工具函数
    "create_logger",
]
