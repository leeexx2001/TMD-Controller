# -*- coding: utf-8 -*-
"""
TMD Controller - Twitter Media Downloader Controller

模块化重构版本 v7.0.0

使用方式:
    python -m tmdc              # 启动交互式菜单
    python -m tmdc --version    # 显示版本信息
    python -m tmdc --status     # 显示配置状态
"""

__version__ = "7.0.0"
__author__ = "TMD Team"


def __getattr__(name: str):
    if name == "VERSION":
        from .constants import VERSION

        return VERSION
    elif name == "Constants":
        from .constants import Constants

        return Constants
    elif name == "C":
        from .constants import C

        return C
    elif name in ("TMDError", "ConfigError", "DownloadError", "DatabaseError", "ValidationError"):
        from . import exceptions

        return getattr(exceptions, name)
    elif name == "main":
        from .__main__ import main

        return main
    elif name == "Container":
        from .container import Container

        return Container
    elif name == "get_service":
        from .container import get_service

        return get_service
    elif name == "TMDConfig":
        from .config.config import TMDConfig

        return TMDConfig
    elif name == "CookieService":
        from .services.cookie_service import CookieService

        return CookieService
    elif name == "DatabaseService":
        from .services.database_service import DatabaseService

        return DatabaseService
    elif name == "DownloadService":
        from .services.download_service import DownloadService

        return DownloadService
    elif name == "ProxyService":
        from .services.proxy_service import ProxyService

        return ProxyService
    elif name == "RemedyService":
        from .services.remedy_service import RemedyService

        return RemedyService
    elif name == "TimestampService":
        from .services.timestamp_service import TimestampService

        return TimestampService
    elif name == "UIHelper":
        from .ui.ui_helper import UIHelper

        return UIHelper
    elif name == "InputParser":
        from .parsers.input_parser import InputParser

        return InputParser
    elif name == "TMDLogParser":
        from .parsers.log_parser import TMDLogParser

        return TMDLogParser
    elif name in (
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
        "DownloadResult",
        "UserInfo",
        "ListInfo",
        "ProxyStatus",
        "CookieInfo",
        "BatchConfig",
        "MenuOption",
        "PathLike",
        "JsonValue",
        "CookieDict",
        "T",
        "TConfig",
        "TService",
        "create_logger",
    ):
        from . import tmd_types

        return getattr(tmd_types, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "VERSION",
    "__version__",
    "__author__",
    "main",
    "Constants",
    "C",
    "TMDError",
    "ConfigError",
    "DownloadError",
    "DatabaseError",
    "ValidationError",
    "Container",
    "get_service",
    "TMDConfig",
    "CookieService",
    "DatabaseService",
    "DownloadService",
    "ProxyService",
    "RemedyService",
    "TimestampService",
    "UIHelper",
    "InputParser",
    "TMDLogParser",
]
