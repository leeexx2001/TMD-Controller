#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TMD Controller 主入口模块

提供命令行入口点，支持 `python -m tmdc` 方式运行。

Example:
    $ python -m tmdc
    $ python -m tmdc --help
    $ python -m tmdc --version
    $ python -m tmdc -u elonmusk -H
"""

from __future__ import annotations

# 标准库
import logging
import subprocess
import sys
import warnings
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

# 第三方库（无）

# 抑制 requests 库的 urllib3 版本警告
warnings.filterwarnings(
    "ignore", message="urllib3 .* or chardet .* doesn't match a supported version!"
)

# 本地模块


def main(argv: Optional[list] = None) -> int:
    """
    主入口函数

    Args:
        argv: 命令行参数列表（用于测试），None 表示使用 sys.argv[1:]

    Returns:
        退出码 (0=成功, 非0=失败)
    """
    from .cli import CLIHandler
    from .config.config import TMDConfig
    from .constants import VERSION
    from .container import Container
    from .ui.ui_helper import UIHelper

    if argv is None:
        argv = sys.argv[1:]

    # 提前解析 -c/--config 参数
    custom_config_path = _extract_config_path(argv)
    if custom_config_path:
        config = TMDConfig(custom_config_path=custom_config_path)
    else:
        config = TMDConfig()

    # 初始化日志
    logger = logging.getLogger("TMDController")

    # 检查调试模式
    debug = "-d" in argv or "--debug" in argv or "--dbg" in argv
    log_level = logging.DEBUG if debug else logging.INFO

    # 确保日志目录存在
    config.log_dir.mkdir(parents=True, exist_ok=True)

    # 配置日志处理器
    handlers = []

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    handlers.append(console_handler)

    # 文件处理器（RotatingFileHandler）
    file_handler = RotatingFileHandler(
        config.log_file,
        maxBytes=config.log_max_bytes,
        backupCount=config.log_backup_count,
        encoding="utf-8",
    )
    file_log_level = (
        logging.DEBUG if debug else getattr(logging, config.log_level, logging.INFO)
    )
    file_handler.setLevel(file_log_level)
    handlers.append(file_handler)

    # 配置日志格式
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    for handler in handlers:
        handler.setFormatter(formatter)

    # 配置根日志记录器
    logging.basicConfig(level=log_level, handlers=handlers)
    logger.setLevel(log_level)

    # 备份数据库（如果存在）
    if config.db_path and config.db_path.exists():
        from .utils import backup_foo_db

        backup_foo_db(config.db_path, logger=logger)

    # 初始化 UI
    ui = UIHelper()

    # 查找 TMD 可执行文件
    executable_path = _find_tmd_executable()
    if executable_path:
        logger.info(f"找到 TMD 可执行文件: {executable_path}")
    else:
        logger.warning("未找到 TMD 可执行文件")

    # 初始化容器和服务
    container = Container.get_instance()
    _register_services(container, config, logger, ui, executable_path)

    # 处理 --status 特殊参数（不通过 CLIHandler）
    if "--status" in argv or "-s" in argv:
        return _show_status(config, ui)

    # 使用 CLIHandler 处理
    cli_handler = CLIHandler(container)
    result = cli_handler.run(argv)

    # 如果返回 -1，表示需要启动交互模式
    if result == -1:
        return _start_interactive_menu(
            container=container,
            config=config,
            logger=logger,
            ui=ui,
            executable_path=executable_path,
        )

    return result


def _extract_config_path(argv: list) -> Optional[Path]:
    """
    从参数中提取配置文件路径

    Args:
        argv: 命令行参数列表

    Returns:
        配置文件路径，如果未指定返回 None
    """
    for i, arg in enumerate(argv):
        if arg in ("-c", "--config") and i + 1 < len(argv):
            return Path(argv[i + 1])
        elif arg.startswith("--config="):
            return Path(arg.split("=", 1)[1])
    return None


def _show_status(config, ui) -> int:
    """
    显示配置状态

    Args:
        config: 配置实例
        ui: UI 辅助实例

    Returns:
        退出码
    """
    ui.clear_screen()
    ui.show_header("配置状态")

    print(f"\n配置文件: {config.config_file}")
    print(f"下载路径: {config.root_path or '未设置'}")
    print(f"代理状态: {'已启用' if config.use_proxy else '未启用'}")
    if config.use_proxy:
        print(f"代理地址: {config.proxy_hostname}:{config.proxy_tcp_port}")
    print(f"最大线程数: {config.max_download_routine}")
    print(f"批量大小: {config.file_batch_size}")
    print(f"固定列表: {len(config.quick_list_ids)} 个")

    auth_status = "已设置" if config.auth_token else "未设置"
    ct0_status = "已设置" if config.ct0 else "未设置"
    print("\n认证状态:")
    print(f"  auth_token: {auth_status}")
    print(f"  ct0: {ct0_status}")

    ui.pause()
    return 0


def _start_interactive_menu(
    container,
    config,
    logger: logging.Logger,
    ui,
    executable_path: Optional[Path],
) -> int:
    """
    启动交互式菜单

    Args:
        container: 依赖注入容器
        config: 配置实例
        logger: 日志实例
        ui: UI 辅助实例
        executable_path: TMD 可执行文件路径

    Returns:
        退出码
    """
    from .constants import VERSION
    from .parsers.log_parser import TMDLogParser

    # 显示启动界面
    ui.show_header("TMD Controller")
    print(f"\n版本: {VERSION}")

    if executable_path:
        print(f"TMD 核心: {executable_path}")
    else:
        print("⚠️  未找到 TMD 可执行文件，部分功能不可用")

    print(f"配置文件: {config.config_file}")
    print()

    # 获取服务实例
    download_service = container.resolve("download_service")
    database_service = container.resolve("database_service")
    cookie_service = container.resolve("cookie_service")
    proxy_service = container.resolve("proxy_service")
    remedy_service = container.resolve("remedy_service")
    timestamp_service = container.resolve("timestamp_service")

    # 创建子菜单实例
    from .menus.advanced_menu import AdvancedMenu
    from .menus.config_menu import ConfigMenu
    from .menus.resume_menu import ResumeMenu
    from .menus.timestamp_menu import TimestampMenu

    config_menu = ConfigMenu(
        ui, logger, config, cookie_service, proxy_service, download_service, database_service
    )
    resume_menu = ResumeMenu(ui, logger, config, download_service, remedy_service)
    timestamp_menu = TimestampMenu(ui, logger, config, database_service, timestamp_service)
    advanced_menu = AdvancedMenu(
        ui, logger, config, download_service, database_service, resume_menu, timestamp_menu, timestamp_service
    )

    # 创建菜单处理器字典
    menu_handlers = {
        "config": config_menu.show,
        "advanced": advanced_menu.show,
        "resume": resume_menu.show,
        "logs": lambda: _show_logs(ui, config, logger),
        "help": lambda: _show_help(ui),
    }

    # 启动主菜单
    from .menus.main_menu import MainMenu

    main_menu = MainMenu(
        ui=ui,
        logger=logger,
        config=config,
        download_service=download_service,
        database_service=database_service,
        cookie_service=cookie_service,
        proxy_service=proxy_service,
        executable_path=executable_path,
        config_exists=config.config_file.exists(),
        log_parser=TMDLogParser(config.log_file) if executable_path else None,
        menu_handlers=menu_handlers,
    )

    try:
        main_menu.show()
    except KeyboardInterrupt:
        print("\n\n用户中断，正在退出...")
        return 130
    finally:
        # 确保日志处理器被正确关闭，加快退出速度
        _shutdown_logging()

    return 0


def _shutdown_logging() -> None:
    """关闭所有日志处理器，确保快速退出"""
    logger = logging.getLogger("TMDController")
    for handler in logger.handlers[:]:
        handler.flush()
        handler.close()
        logger.removeHandler(handler)

    # 关闭根日志记录器的所有处理器
    root = logging.getLogger()
    for handler in root.handlers[:]:
        handler.flush()
        handler.close()
        root.removeHandler(handler)


def _find_tmd_executable() -> Optional[Path]:
    """查找 TMD 可执行文件"""
    from .constants import C

    # 1. 检查 PyInstaller 打包的资源目录 (MEIPASS)
    if hasattr(sys, '_MEIPASS'):
        meipass = Path(sys._MEIPASS)
        bundled_tmd = meipass / "tmdc" / "tmd.exe"
        if bundled_tmd.exists():
            return bundled_tmd

    # 2. 尝试使用 where 命令
    for name in ["tmd.exe", "tmd"]:
        try:
            result = subprocess.run(
                ["where", name], capture_output=True, text=True, timeout=C.PROXY_TIMEOUT
            )
            if result.returncode == 0:
                path = Path(result.stdout.strip().split("\n")[0])
                if path.exists():
                    return path
        except Exception:
            pass

    # 3. 检查同级目录
    script_dir = Path(__file__).parent.resolve()
    for name in ["tmd.exe", "tmd"]:
        path = script_dir.parent / name
        if path.exists() and path.is_file():
            return path

    # 4. 检查 tmd 子目录
    for name in ["tmd.exe", "tmd"]:
        path = script_dir.parent / "tmd" / name
        if path.exists() and path.is_file():
            return path

    # 5. 检查当前包目录（开发模式）
    bundled_in_pkg = script_dir / "tmd.exe"
    if bundled_in_pkg.exists():
        return bundled_in_pkg

    return None


def _show_logs(ui, config, logger) -> None:
    """显示日志查看器"""
    from .parsers.log_parser import TMDLogParser

    ui.clear_screen()
    ui.show_header("日志查看器")

    log_parser = TMDLogParser(config.log_file)
    logs = log_parser.get_tail(lines=50)

    if not logs:
        print("暂无日志记录")
    else:
        print(logs)

    ui.pause()


def _show_help(ui) -> None:
    """显示帮助信息"""
    ui.clear_screen()
    ui.show_header("帮助信息")

    print("""
TMD Controller - Twitter Media Downloader 控制程序

主菜单选项:
  [1] 快捷输入    - 智能识别URL/用户名/列表ID开始下载
  [2] 高级选项    - 精确控制、批量、文件、组合、时间戳管理

  [R] 恢复下载    - 续传未完成任务
  [Q] 快速下载    - 顺序下载所有配置的固定列表
  
  [C] 配置向导    - 配置 TMD 核心参数
  [L] 查看日志    - 查看 TMD 运行日志
  
  [H] 帮助        - 查看此帮助信息
  [0] 退出        - 退出程序

快捷输入格式:
  - URL: https://x.com/username
  - 用户名: @username 或 username
  - 列表ID: 1234567890 (10位以上数字)
  - Name格式: Name(username)

配置文件位置:
  - 主配置: ~/.tmd2/conf.yaml
  - Cookie: ~/.tmd2/additional_cookies.yaml
  - 数据库: {root_path}/.data/foo.db (root_path 在主配置中设置)
""")
    ui.pause()


def _register_services(container, config, logger, ui, executable_path):
    """注册服务到容器"""
    from .parsers.log_parser import TMDLogParser
    from .services import (
        CookieService,
        DatabaseService,
        DownloadService,
        ProxyService,
        RemedyService,
        TimestampService,
    )

    # 注册核心服务
    if not container.has("config"):
        container.register("config", config)
    if not container.has("logger"):
        container.register("logger", logger)
    if not container.has("ui"):
        container.register("ui", ui)

    # 注册业务服务
    if not container.has("database_service"):
        container.register_factory(
            "database_service",
            lambda: DatabaseService(config=config, logger=logger),
        )

    if not container.has("proxy_service"):
        container.register_factory(
            "proxy_service",
            lambda: ProxyService(config=config, logger=logger),
        )

    if not container.has("cookie_service"):
        container.register_factory(
            "cookie_service",
            lambda: CookieService(config=config, logger=logger),
        )

    if not container.has("download_service"):
        container.register_factory(
            "download_service",
            lambda: DownloadService(
                config=config,
                logger=logger,
                executable_path=executable_path,
                log_parser=TMDLogParser(config.log_file),
                database_service=container.resolve("database_service"),
            ),
        )

    if not container.has("timestamp_service"):
        db = container.resolve("database_service")
        ds = container.resolve("download_service")
        container.register_factory(
            "timestamp_service",
            lambda: TimestampService(
                config=config,
                logger=logger,
                database_service=db,
                download_service=ds,
            ),
        )

    if not container.has("remedy_service"):
        ds = container.resolve("download_service")
        db = container.resolve("database_service")
        container.register_factory(
            "remedy_service",
            lambda: RemedyService(
                config=config,
                logger=logger,
                download_service=ds,
                database_service=db,
            ),
        )


if __name__ == "__main__":
    # 当直接运行此文件时，确保包路径正确
    if __package__ is None:
        script_dir = Path(__file__).resolve().parent
        sys.path.insert(0, str(script_dir.parent))
        __package__ = "tmdc"
    sys.exit(main())
