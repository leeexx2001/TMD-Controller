# -*- coding: utf-8 -*-
"""
TMD Controller PyInstaller Spec 文件

生成命令:
    pyi-makespec --onefile --name tmdc tmdc/__main__.py
"""

from pathlib import Path

block_cipher = None

# 动态检查 tmd.exe 是否存在
# 支持位置:
#   1. tmdc/tmd.exe (tmdc 包目录)
#   2. tmd.exe (项目根目录 / build_exe.py 同目录 / tmdc 同目录)
binaries = []
for tmd_path in [Path('tmdc/tmd.exe'), Path('tmd.exe')]:
    if tmd_path.exists():
        binaries.append((str(tmd_path), 'tmdc'))
        break

a = Analysis(
    ['tmdc/__main__.py'],
    pathex=[],
    binaries=binaries,
    datas=[],
    hiddenimports=[
        'tmdc.cli.cli_handler',
        'tmdc.config.config',
        'tmdc.constants',
        'tmdc.container',
        'tmdc.exceptions',
        'tmdc.menus.advanced_menu',
        'tmdc.menus.base_menu',
        'tmdc.menus.config_menu',
        'tmdc.menus.cookie_menu',
        'tmdc.menus.main_menu',
        'tmdc.menus.path_menu',
        'tmdc.menus.proxy_menu',
        'tmdc.menus.quick_list_menu',
        'tmdc.menus.resume_menu',
        'tmdc.menus.timestamp_menu',
        'tmdc.parsers.date_parser',
        'tmdc.parsers.delay_parser',
        'tmdc.parsers.input_parser',
        'tmdc.parsers.log_parser',
        'tmdc.services.cookie_service',
        'tmdc.services.database_service',
        'tmdc.services.download_service',
        'tmdc.services.proxy_service',
        'tmdc.services.remedy_service',
        'tmdc.services.timestamp_service',
        'tmdc.tmd_types',
        'tmdc.ui.config_checker',
        'tmdc.ui.remedy_progress',
        'tmdc.ui.ui_helper',
        'tmdc.utils.file_io',
        'tmdc.utils.formatters',
        'tmdc.utils.path_utils',
        'tmdc.utils.patterns',
        'tmdc.utils.text_utils',
        'tmdc.utils.validators.auth',
        'tmdc.utils.validators.cookie',
        'tmdc.utils.validators.list_id',
        'tmdc.utils.validators.path',
        'tmdc.utils.validators.proxy',
        'tmdc.utils.validators.timestamp',
        'tmdc.utils.validators.username',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除测试模块
        'pytest',
        '_pytest',
        'unittest',
        'test',
        'tests',
        # 排除调试模块
        'pdb',
        'pudb',
        'ipdb',
        'bdb',
        'code',
        'codeop',
        # 排除文档/帮助
        'pydoc',
        'pydoc_data',
        # 排除 Tkinter (GUI)
        'tkinter',
        'Tkinter',
        '_tkinter',
        # 排除其他GUI
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'wx',
        'wxPython',
        # 排除开发工具
        'black',
        'isort',
        'flake8',
        'mypy',
        'pre_commit',
        # 排除网络调试
        'http.server',
        'xmlrpc',
        'wsgiref',
        # 排除数据库(如果不用)
        'sqlite3.test',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='tmdc',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
