# -*- coding: utf-8 -*-
"""
路径处理工具模块

提供文件路径处理相关功能，包括文件名清理、唯一路径生成、扩展名提取等。
"""

from __future__ import annotations

# 标准库
from pathlib import Path
from typing import List
from urllib.parse import urlparse

# 本地模块
from .patterns import URL_PATTERN_RE, WIN_INVALID_CHARS_RE

# Windows 保留文件名
_WINDOWS_RESERVED_NAMES: frozenset[str] = frozenset(
    {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    }
)


def sanitize_win_filename(name: str, max_bytes: int = 155) -> str:
    """清理 Windows 文件名

    参考 TMD Go 实现: internal/utils/fs.go WinFileName
    - 移除 URL: reUrl.ReplaceAllString(name, "")
    - 移除非法字符: reWinNonSupport.ReplaceAllString(name, "")
    - 换行符处理: \\r 跳过, \\n 替换为空格
    - 长度限制: 默认 155 字节（预留空间给路径和扩展名）

    Args:
        name: 原始文件名
        max_bytes: 最大字节数（默认155，为Windows路径预留空间）

    Returns:
        清理后的文件名

    Examples:
        >>> sanitize_win_filename("test<file>.txt")
        'testfile.txt'
        >>> sanitize_win_filename("https://example.com/page")
        ''
        >>> sanitize_win_filename("CON")
        'CON_'
    """
    name = URL_PATTERN_RE.sub("", name)

    name = WIN_INVALID_CHARS_RE.sub("", name)

    result: List[str] = []
    byte_length = 0

    for char in name:
        if char == "\r":
            continue
        elif char == "\n":
            char = " "

        char_bytes = len(char.encode("utf-8"))
        if byte_length + char_bytes > max_bytes:
            break

        result.append(char)
        byte_length += char_bytes

    name = "".join(result)

    name = name.strip(". ")

    if name.upper() in _WINDOWS_RESERVED_NAMES:
        name = f"{name}_"

    return name if name else "untitled"


def unique_path(filepath: Path) -> Path:
    """生成唯一路径，处理文件名冲突

    参考 TMD UniquePath 实现，当文件已存在时自动添加序号。

    Args:
        filepath: 原始文件路径

    Returns:
        唯一的文件路径

    Examples:
        >>> import tempfile
        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     p = Path(tmpdir) / "test.txt"
        ...     p.touch()
        ...     result = unique_path(p)
        ...     result.name
        'test(1).txt'
    """
    while filepath.exists():
        dir_path = filepath.parent
        ext = filepath.suffix
        stem = filepath.stem

        if stem.endswith(")"):
            left = stem.rfind("(")
            if left != -1:
                try:
                    index = int(stem[left + 1 : -1])
                    new_stem = f"{stem[:left]}({index + 1})"
                    filepath = dir_path / f"{new_stem}{ext}"
                    continue
                except ValueError:
                    pass

        filepath = dir_path / f"{stem}(1){ext}"

    return filepath


def get_ext_from_url(url: str) -> str:
    """从 URL 获取文件扩展名

    参考 TMD 实现，只从 URL 路径提取扩展名。

    Args:
        url: 文件 URL

    Returns:
        文件扩展名（包含点号），无法提取时返回 ".bin"

    Examples:
        >>> get_ext_from_url("https://example.com/image.jpg")
        '.jpg'
        >>> get_ext_from_url("https://example.com/video")
        '.bin'
        >>> get_ext_from_url("https://example.com/path/to/file.mp4?query=1")
        '.mp4'
    """
    parsed = urlparse(url)
    ext = Path(parsed.path).suffix.lower()
    return ext if ext else ".bin"


def generate_filename_from_text(text: str, ext: str) -> str:
    """从文本生成文件名

    Args:
        text: 文本内容
        ext: 文件扩展名（包含点号）

    Returns:
        生成的文件名

    Examples:
        >>> generate_filename_from_text("Hello World", ".txt")
        'Hello World.txt'
        >>> generate_filename_from_text("", ".txt")
        'tweet.txt'
        >>> generate_filename_from_text("https://invalid.com", ".txt")
        'tweet.txt'
    """
    clean_text = sanitize_win_filename(text)

    if not clean_text:
        clean_text = "tweet"

    return f"{clean_text}{ext}"


def normalize_path(path: str) -> str:
    """标准化路径分隔符为 Windows 反斜杠 '\\'

    与 TMD Go 保持一致。

    Args:
        path: 原始路径

    Returns:
        标准化后的路径

    Examples:
        >>> normalize_path("D:/Downloads/twitter")
        'D:\\\\Downloads\\\\twitter'
    """
    return path.replace("/", "\\")


__all__ = [
    "sanitize_win_filename",
    "unique_path",
    "get_ext_from_url",
    "generate_filename_from_text",
    "normalize_path",
]
