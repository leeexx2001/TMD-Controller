#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
恢复菜单模块

从原始文件 TMD_Controller_v6.7.2.py 第 5568-5701 行迁移。
提供恢复下载、补救下载等功能的菜单界面。

主要功能：
- 自动恢复下载（循环模式）
- 单次恢复下载
- 补救下载（绕过 TMD）
- 失败任务统计
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Optional

from ..constants import C
from .base_menu import BaseMenu

if TYPE_CHECKING:
    import logging

    from ..services.download_service import DownloadService
    from ..services.remedy_service import RemedyService
    from ..tmd_types import IConfig, IUIHelper


class ResumeMenu(BaseMenu):
    """恢复菜单

    提供恢复下载、补救下载等功能的菜单界面。

    Attributes:
        ui: UI 辅助实例
        logger: 日志实例
        config: 配置实例
        download_service: 下载服务实例
        remedy_service: 补救服务实例

    Example:
        >>> from tmdc.menus.resume_menu import ResumeMenu
        >>> menu = ResumeMenu(ui, logger, config, download_service, remedy_service)
        >>> menu.show()
    """

    def __init__(
        self,
        ui: "IUIHelper",
        logger: "logging.Logger",
        config: "IConfig",
        download_service: "DownloadService",
        remedy_service: "RemedyService",
    ) -> None:
        """
        初始化恢复菜单

        Args:
            ui: UI 辅助实例
            logger: 日志实例
            config: 配置实例
            download_service: 下载服务实例
            remedy_service: 补救服务实例
        """
        super().__init__(ui, logger, config)
        self.download_service = download_service
        self.remedy_service = remedy_service

    def show(self) -> None:
        """显示恢复菜单"""
        self.ui.clear_screen()
        self.ui.show_header("恢复未完成下载")

        if not self._check_config_or_return():
            return

        print("继续下载之前失败或未完成的任务。")
        print("[1] 自动恢复下载    → 循环后自动补救下载")
        print("[2] 恢复下载        → 单次恢复，不循环")
        print("[3] 补救下载        → 绕开TMD，直接下载")
        print("[4] 失败任务统计    → 显示失败任务详情")
        print("[0] 返回主菜单\n")

        choice = self.ui.safe_input("请选择 [1-4,0]: ", allow_empty=True)
        if choice is None:
            return
        choice = choice.upper()

        if choice == "":
            choice = "1"

        if choice == "0":
            return
        elif choice == "1":
            self._run_auto_loop()
        elif choice == "2":
            self._run_interactive_loop()
        elif choice == "3":
            self._force_remedy()
        elif choice == "4":
            self._check_stats()

    def _run_interactive_loop(self) -> None:
        """单次恢复下载，不循环"""
        print("📝 正在从数据库恢复所有待处理下载...")
        exit_code, _, _ = self.download_service.run_tmd(args=[])

        if exit_code == 0:
            print("✅ 恢复下载完成！")
        else:
            print("❌ 恢复下载失败")
            print("📝 可随时恢复 - 已下载的文件是安全的")
            print("💡 使用 [R] 恢复下载 可续传未完成任务")
            self.logger.warning("恢复下载失败")

        self.ui.pause()

    def _run_auto_loop(self) -> None:
        """自动恢复下载（智能循环，自动连续恢复，结束后执行补救下载）"""
        round_count = 0
        last_pending: Optional[int] = None
        stagnant_count = 0
        auto_mode_completed = False

        print("\n✅ 已开启自动循环模式（结束后将执行补救下载）")
        print("💡 按 Ctrl+C 可随时安全暂停\n")

        while True:
            round_count += 1

            print()
            self.ui.print_separator()
            if round_count > 1:
                print(f"🔄 第 {round_count} 轮恢复...")
            self.ui.print_separator()

            print("📝 正在从数据库恢复所有待处理下载...")
            exit_code, _, _ = self.download_service.run_tmd(args=[])

            if exit_code == 0:
                print("✅ 当前轮次下载完成！")
            else:
                print("❌ 当前轮次下载失败")

            pending = self.download_service.check_pending_tweets(self.config.root_path)

            if pending is None or pending == 0:
                print("\n✅ 所有待处理下载已完成！")
                break

            print(f"\n📝 仍有 {pending} 个待处理推文")

            if pending == last_pending:
                stagnant_count += 1
                if stagnant_count >= C.RESUME_MAX_STAGNANT - 1:
                    print(f"\n⚠️ 连续 {C.RESUME_MAX_STAGNANT} 轮待处理数量未变化 ({pending} 个)")
                    print("💡 这些任务可能无法下载（推文已删除/账号被封等）")
                    print("📝 自动循环结束，准备执行补救下载...")
                    auto_mode_completed = True
                    break
            else:
                stagnant_count = 0

            last_pending = pending

            if round_count >= C.RESUME_MAX_ROUNDS:
                print(f"\n⚠️ 已达到最大轮数限制 ({C.RESUME_MAX_ROUNDS} 轮)")
                print(f"📝 仍有 {pending} 个待处理推文")
                print("📝 自动循环结束，准备执行补救下载...")
                auto_mode_completed = True
                break

            self.ui.delay(seconds=C.RESUME_RETRY_SEC, message=f"⏳ {C.RESUME_RETRY_SEC}秒后继续下一轮...", allow_skip=True)

        if auto_mode_completed:
            print()
            self.ui.print_separator()
            print("🔄 开始补救下载（绕开TMD）...")
            self.ui.print_separator()
            self._force_remedy()
        else:
            self.ui.pause()

    def _check_stats(self) -> None:
        """检查统计，使用 DownloadService.check_pending_tweets"""
        print("📝 正在检查失败/待处理任务...")

        self.logger.info("查看失败任务统计")

        pending = self.download_service.check_pending_tweets(self.config.root_path)

        if pending is None:
            print("❌ 无法读取统计信息")
        elif pending == 0:
            print("✅ 没有待处理的失败推文")
        else:
            print(f"📝 待处理推文: {pending} 个")
            print("💡 使用 [R] 恢复下载 可续传未完成任务")

        self.ui.print_separator()
        self.ui.pause()

    def _force_remedy(self) -> None:
        """补救下载：直接从 errors.json 下载媒体（绕开TMD）"""
        from ..ui.remedy_progress import TerminalProgressCallback

        callback = TerminalProgressCallback()
        success = self.remedy_service.execute(progress_callback=callback)
        if success:
            self.logger.info("补救下载完成")
        else:
            self.logger.warning("补救下载失败或部分失败")


__all__ = ["ResumeMenu"]
