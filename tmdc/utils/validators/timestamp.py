# -*- coding: utf-8 -*-
"""时间戳参数解析模块

注意：此模块包含 UI 交互逻辑（handle_numeric_id_ambiguity）。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Optional, Tuple

if TYPE_CHECKING:
    from tmdc.tmd_types import IUIHelper


def parse_timestamp_target(arg_str: str) -> Tuple[Optional[Dict[str, str]], Optional[str]]:
    """解析时间戳参数中的目标部分

    支持格式：
    - user:username,7d -> ({'type': 'user', 'id': 'username'}, '7d')
    - list:123456,2024-01-15 -> ({'type': 'list', 'id': '123456'}, '2024-01-15')
    - @username -> ({'type': 'user', 'id': 'username'}, None)

    Args:
        arg_str: 参数字符串，格式如 "user:elonmusk,7d" 或 "list:123"

    Returns:
        Tuple[Optional[Dict], Optional[str]]:
            (target_dict, time_part) 或 (None, None) 如果解析失败
            target_dict: {"type": "user"|"list", "id": str}

    Examples:
        >>> parse_timestamp_target("user:elonmusk,7d")
        ({'type': 'user', 'id': 'elonmusk'}, '7d')
        >>> parse_timestamp_target("list:1234567890")
        ({'type': 'list', 'id': '1234567890'}, None)
        >>> parse_timestamp_target("@elonmusk")
        ({'type': 'user', 'id': 'elonmusk'}, None)
    """
    if not arg_str or not arg_str.strip():
        return None, None

    arg_str = arg_str.strip()

    if "," in arg_str:
        parts = arg_str.split(",", 1)
        target_part = parts[0].strip()
        time_part = parts[1].strip() if len(parts) > 1 else None
    else:
        target_part = arg_str
        time_part = None

    if target_part.startswith("user:"):
        username = target_part[5:].strip()
        if not username:
            print("user: 后需要指定用户名")
            return None, None
        return {"type": "user", "id": username}, time_part

    elif target_part.startswith("list:"):
        list_id = target_part[5:].strip()
        if not list_id.isdigit():
            print(f"列表ID必须是数字，当前: {list_id}")
            return None, None
        return {"type": "list", "id": list_id}, time_part

    elif target_part.startswith("@"):
        username = target_part[1:].strip()
        if not username:
            print("@ 后需要指定用户名")
            return None, None
        return {"type": "user", "id": username}, time_part

    else:
        print(f"无效的目标格式: {target_part}")
        print("格式示例: user:elonmusk | list:1234567890 | @elonmusk")
        print("       必须带前缀: user: 或 list: 或使用 @ 简写用户")
        return None, None


def handle_numeric_id_ambiguity(
    value: str,
    ui: "IUIHelper",
    default_as_list: bool = True,
    mode: str = "both",
) -> Tuple[str, str]:
    """处理数字 ID 的歧义性（无法区分用户 ID 还是列表 ID）

    显示选择菜单让用户选择是用户 ID 还是列表 ID。

    Args:
        value: 数字 ID 字符串
        ui: UI 辅助实例
        default_as_list: 默认作为列表 ID 处理（回车选择），仅 mode="both" 时有效
        mode: 选择模式
            - "both": 可选用户/列表（默认）
            - "user_only": 仅确认用户，可取消
            - "list_only": 仅确认列表，可取消

    Returns:
        Tuple[str, str]: (类型, 值)
            - 类型: "user" | "list" | ""（取消）
            - 值: 原始数字 ID
    """
    print(f"\n📝 识别：数字 ID: {value}")

    if mode == "both":
        print("无法自动区分这是用户 ID 还是列表 ID")
        if default_as_list:
            print("  [回车] 列表 ID (--list)")
            print("  [1]    用户 ID (--user)")
        else:
            print("  [回车] 用户 ID (--user)")
            print("  [1]    列表 ID (--list)")

        choice = ui.safe_input("请选择: ", allow_empty=True)

        if default_as_list:
            if choice == "1":
                return ("user", value)
            return ("list", value)
        else:
            if choice == "1":
                return ("list", value)
            return ("user", value)

    elif mode == "user_only":
        print("此模式仅支持用户 ID")
        print("  [回车] 确认是用户 ID")
        print("  [N]   取消")
        choice = ui.safe_input("请选择: ", allow_empty=True)
        if choice and choice.upper() == "N":
            return ("", value)
        return ("user", value)

    elif mode == "list_only":
        print("此模式仅支持列表 ID")
        print("  [回车] 确认是列表 ID")
        print("  [N]   取消")
        choice = ui.safe_input("请选择: ", allow_empty=True)
        if choice and choice.upper() == "N":
            return ("", value)
        return ("list", value)

    return ("", value)


__all__ = ["parse_timestamp_target", "handle_numeric_id_ambiguity"]
