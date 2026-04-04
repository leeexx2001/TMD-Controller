# -*- coding: utf-8 -*-
"""路径验证模块"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple, Union


def validate_path(
    path: Union[str, Path], must_exist: bool = False, check_parent: bool = True
) -> Tuple[bool, str]:
    """验证文件/目录路径

    Args:
        path: 需要验证的路径（字符串或 Path 对象）
        must_exist: 是否要求路径必须存在，默认为 False
        check_parent: 是否检查父目录存在性，默认为 True

    Returns:
        Tuple[bool, str]: (是否有效, 错误信息)

    Examples:
        >>> validate_path("/tmp/test.txt", must_exist=False)
        (True, '')
        >>> validate_path("/nonexistent/path", must_exist=True)
        (False, '路径不存在: /nonexistent/path')
    """
    if not path:
        return False, "路径不能为空"

    try:
        p = Path(path) if isinstance(path, str) else path
    except Exception as e:
        return False, f"路径格式无效: {e}"

    if must_exist and not p.exists():
        return False, f"路径不存在: {p}"

    if check_parent and not p.parent.exists():
        return False, f"父目录不存在: {p.parent}"

    return True, ""


__all__ = ["validate_path"]
