# -*- coding: utf-8 -*-
"""
补救下载进度回调实现

提供默认的终端进度输出实现。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from tmdc.tmd_types import IProgressCallback


class TerminalProgressCallback:
    """终端进度回调

    将进度信息输出到终端。

    Example:
        >>> callback = TerminalProgressCallback()
        >>> callback.on_start(10, "开始补救下载")
        >>> callback.on_item_success("tweet_123", "tweet_123: media.jpg")
        >>> callback.on_complete(9, 1)
    """

    def __init__(self) -> None:
        self._cancelled = False
        self._success_items: List[str] = []
        self._failed_items: List[str] = []

    def on_start(self, total: int, message: str) -> None:
        print(f"\n⚠️  补救下载模式（绕开TMD）")
        print(f"📝 {message}")
        print(f"💡 发现 {total} 个失败推文待处理")
        print("   适用于 TMD 多次恢复仍无法完成的顽固任务\n")

    def on_progress(self, current: int, message: str) -> None:
        if message:
            print(message)

    def on_item_success(self, item_id: str, message: str) -> None:
        self._success_items.append(item_id)
        if message:
            print(f"      ✓ {message}")

    def on_item_failed(self, item_id: str, error: str) -> None:
        self._failed_items.append(item_id)
        print(f"      ✗ {error}")

    def on_complete(self, success_count: int, fail_count: int) -> None:
        print(f"\n📊 下载完成：成功 {success_count}，失败 {fail_count}")
        if fail_count == 0:
            print("✅ 所有失败推文已成功下载！")
        else:
            print(f"📝 仍有 {fail_count} 个推文无法下载")

    def is_cancelled(self) -> bool:
        return self._cancelled

    def cancel(self) -> None:
        self._cancelled = True


class SilentProgressCallback:
    """静默进度回调

    不产生任何输出的回调实现。
    适用于无头模式（headless）或需要静默运行的场景。

    Example:
        >>> callback = SilentProgressCallback()
        >>> callback.on_start(10, "开始补救下载")
        >>> # 没有任何输出
        >>> callback.on_complete(9, 1)
        >>> # 没有任何输出
    """

    def on_start(self, total: int, message: str) -> None:
        pass

    def on_progress(self, current: int, message: str) -> None:
        pass

    def on_item_success(self, item_id: str, message: str) -> None:
        pass

    def on_item_failed(self, item_id: str, error: str) -> None:
        pass

    def on_complete(self, success_count: int, fail_count: int) -> None:
        pass

    def is_cancelled(self) -> bool:
        return False


__all__ = ["TerminalProgressCallback", "SilentProgressCallback"]
