# -*- coding: utf-8 -*-
"""
TMD 常量定义模块

从原始文件 TMD_Controller_v6.7.2.py 第 57-96 行提取
"""

VERSION = "7.0.0"


class Constants:
    """
    统一常量管理类

    所有常量按功能分组，便于维护和理解。
    """

    # ========== 验证常量 ==========
    USERNAME_MAX_LEN: int = 15
    """用户名最大长度（Twitter限制）"""

    LIST_ID_MIN_LEN: int = 10
    """列表ID最小长度"""

    COOKIE_MIN_LEN: int = 50
    """Cookie字符串最小长度"""

    MAX_DOWNLOAD_ROUTINE: int = 100
    """最大并行下载数"""

    MIN_BATCH_SIZE: int = 1
    """批量下载最小值"""

    MAX_BATCH_SIZE: int = 50
    """批量下载最大值"""

    # ========== UI常量 ==========
    BATCH_MAX_DISPLAY: int = 5
    """批量显示数量上限"""

    LOG_PAGE_SIZE: int = 20
    """日志分页大小"""

    LOG_MAX_FILES_DISPLAY: int = 15
    """日志文件最大显示数"""

    LOG_DISPLAY_DEFAULT_LINES: int = 50
    """日志默认显示行数"""

    LOG_FILTER_MAX_LINES: int = 100
    """日志过滤最大行数"""

    AUTO_CLOSE_DELAY: int = 8
    """自动关闭延迟（秒）"""

    MAX_QUICK_LIST_INTERVAL: int = 300
    """快速列表最大间隔（秒）"""

    # ========== 系统常量 ==========
    PROXY_TIMEOUT: float = 5.0
    """代理连接超时（秒）"""

    PROXY_CACHE_TTL: float = 5.0
    """代理状态缓存有效期（秒）"""

    COUNTDOWN_INTERVAL: float = 0.1
    """倒计时刷新间隔（秒）"""

    RESUME_RETRY_SEC: int = 2
    """恢复下载重试间隔（秒）"""

    CONFIG_PERMISSION: int = 0o600
    """配置文件权限"""

    UI_WIDTH: int = 62
    """UI显示宽度"""

    RESUME_MAX_ROUNDS: int = 10
    """恢复下载最大轮数"""

    RESUME_MAX_STAGNANT: int = 3
    """停滞检测阈值（连续N轮无变化）"""

    # ========== 补救下载常量 ==========
    REMEDY_TIMEOUT: int = 30
    """下载超时（秒）"""

    REMEDY_MAX_SIZE_MB: int = 800
    """单文件最大大小（MB）"""

    REMEDY_RETRY: int = 2
    """重试次数"""

    # ========== Twitter 常量 ==========
    TWITTER_RESERVED_PATHS: frozenset[str] = frozenset(
        {
            "i",
            "home",
            "explore",
            "notifications",
            "messages",
            "search",
            "settings",
            "compose",
            "login",
            "logout",
            "hashtag",
            "intent",
            "share",
            "followers",
            "following",
        }
    )
    """Twitter 保留路径集合（不能作为用户名）"""


# 常量别名，便于快速访问
C = Constants


__all__ = ["VERSION", "Constants", "C"]
