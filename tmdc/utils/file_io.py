# -*- coding: utf-8 -*-
"""
文件 I/O 工具模块

提供文件操作相关功能，包括原子写入、备份、目录创建、文件读取等。
"""

from __future__ import annotations

# 标准库
import logging
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, List, Optional, Union

if TYPE_CHECKING:
    from tmdc.tmd_types import ILogger

# 第三方库（延迟导入 yaml，避免强制依赖）
try:
    import yaml
except ImportError:
    yaml = None

# 本地模块（无）


def atomic_write_yaml(
    filepath: Path, data: Any, logger: Optional[Union[logging.Logger, "ILogger"]] = None
) -> bool:
    """原子写入 YAML 文件

    使用临时文件模式确保写入操作的原子性，避免写入过程中断导致文件损坏。

    Args:
        filepath: 目标文件路径
        data: 要写入的数据（通常是字典或列表）
        logger: 可选的日志记录器

    Returns:
        bool: 写入是否成功

    Examples:
        >>> from pathlib import Path
        >>> import tempfile
        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     result = atomic_write_yaml(Path(tmpdir) / "test.yaml", {"key": "value"})
        ...     result
        True
    """
    if yaml is None:
        if logger:
            logger.error("原子写入失败: 未安装 PyYAML")
        return False

    temp_path = None
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)

        fd, temp_path = tempfile.mkstemp(
            dir=filepath.parent, prefix=f"{filepath.stem}_", suffix=".tmp"
        )

        os.chmod(temp_path, 0o600)

        with os.fdopen(fd, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

        os.replace(temp_path, filepath)
        return True

    except Exception as e:
        if logger:
            logger.error(f"原子写入失败: {e}")
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except OSError:
                pass
        return False


def backup_foo_db(
    db_path: Path, max_backups: int = 10, logger: Optional[logging.Logger] = None
) -> bool:
    """备份 foo.db 文件，保留最近 N 个备份版本

    Args:
        db_path: 数据库文件路径
        max_backups: 最大备份数量，默认为 10
        logger: 可选的日志记录器

    Returns:
        bool: 备份是否成功

    Examples:
        >>> from pathlib import Path
        >>> import tempfile
        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     db = Path(tmpdir) / "foo.db"
        ...     db.touch()
        ...     result = backup_foo_db(db, max_backups=5)
        ...     result
        True
    """
    try:
        if not db_path or not db_path.exists():
            if logger:
                logger.warning("备份失败: 找不到数据库文件")
            return False

        backup_dir = db_path.parent / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{db_path.stem}_{timestamp}{db_path.suffix}"
        backup_path = backup_dir / backup_name

        shutil.copy2(str(db_path), str(backup_path))

        backup_files = sorted(
            [f for f in backup_dir.glob(f"{db_path.stem}_*{db_path.suffix}") if f.is_file()],
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )

        if len(backup_files) > max_backups:
            for old_backup in backup_files[max_backups:]:
                try:
                    old_backup.unlink()
                    if logger:
                        logger.info(f"已删除旧备份: {old_backup.name}")
                except OSError as e:
                    if logger:
                        logger.warning(f"删除旧备份失败 {old_backup.name}: {e}")

        if logger:
            logger.info(f"数据库已备份: {backup_name} (保留最近 {max_backups} 个版本)")

        return True

    except Exception as e:
        if logger:
            logger.error(f"备份数据库失败: {e}")
        return False


def ensure_dir(path: Union[Path, str]) -> Path:
    """确保目录存在，如果不存在则创建

    Args:
        path: 目录路径（字符串或 Path 对象）

    Returns:
        Path: 目录路径对象

    Examples:
        >>> import tempfile
        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     result = ensure_dir(Path(tmpdir) / "subdir" / "nested")
        ...     result.exists()
        True
    """
    p = Path(path) if isinstance(path, str) else path
    p.mkdir(parents=True, exist_ok=True)
    return p


def read_file_lines(
    filepath: Union[Path, str],
    encoding: str = "utf-8",
    strip_lines: bool = True,
    skip_empty: bool = True,
) -> List[str]:
    """读取文件并返回行列表

    Args:
        filepath: 文件路径
        encoding: 文件编码，默认为 utf-8
        strip_lines: 是否去除每行首尾空白，默认为 True
        skip_empty: 是否跳过空行，默认为 True

    Returns:
        List[str]: 文件行列表

    Raises:
        FileNotFoundError: 文件不存在
        UnicodeDecodeError: 编码错误

    Examples:
        >>> import tempfile
        >>> with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        ...     _ = f.write("line1\\nline2\\n\\nline3\\n")
        ...     temp_path = f.name
        >>> lines = read_file_lines(temp_path)
        >>> lines
        ['line1', 'line2', 'line3']
        >>> import os
        >>> os.unlink(temp_path)
    """
    p = Path(filepath) if isinstance(filepath, str) else filepath

    with open(p, "r", encoding=encoding) as f:
        lines = f.readlines()

    result = []
    for line in lines:
        if strip_lines:
            line = line.strip()
        if skip_empty and not line:
            continue
        result.append(line)

    return result


def get_file_size(filepath: Union[Path, str]) -> int:
    """获取文件大小（字节）

    Args:
        filepath: 文件路径

    Returns:
        int: 文件大小（字节），文件不存在时返回 0

    Examples:
        >>> import tempfile
        >>> with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        ...     _ = f.write("Hello, World!")
        ...     temp_path = f.name
        >>> get_file_size(temp_path)
        13
        >>> import os
        >>> os.unlink(temp_path)
    """
    p = Path(filepath) if isinstance(filepath, str) else filepath

    try:
        return p.stat().st_size
    except (FileNotFoundError, OSError):
        return 0


def get_errors_json_path(root_path: Optional[str]) -> Optional[Path]:
    """获取 errors.json 文件路径

    Args:
        root_path: 下载根目录路径

    Returns:
        errors.json 文件路径，如果 root_path 无效返回 None

    Examples:
        >>> get_errors_json_path("/path/to/downloads")
        PosixPath('/path/to/downloads/.data/errors.json')
        >>> get_errors_json_path(None)
        None
    """
    if not root_path:
        return None
    return Path(root_path) / ".data" / "errors.json"


__all__ = [
    "atomic_write_yaml",
    "backup_foo_db",
    "ensure_dir",
    "read_file_lines",
    "get_file_size",
    "get_errors_json_path",
]
