# -*- coding: utf-8 -*-
"""
TMD 补救服务模块

提供补救下载操作的核心功能。

主要功能：
- 补救下载（绕过 TMD 直接下载）
- 文件名清理和唯一化
- 实体目录查询
"""

from __future__ import annotations

# 标准库
import json
import os
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, cast

if TYPE_CHECKING:
    from types import ModuleType

    from ..tmd_types import (
        IConfig,
        IDatabaseService,
        IDownloadService,
        ILogger,
        IProgressCallback,
        IUIHelper,
    )

# 第三方库（无 - requests 使用延迟导入）

# 本地模块
from ..constants import C
from ..utils.path_utils import generate_filename_from_text, get_ext_from_url, unique_path

_requests: Optional["ModuleType"] = None


def _get_requests() -> Optional["ModuleType"]:
    """延迟导入 requests 模块。

    Returns:
        requests 模块，如果导入失败则返回 None
    """
    global _requests
    if _requests is None:
        try:
            import requests

            _requests = requests
        except ImportError:
            pass
    return _requests


class RemedyService:
    """
    补救服务

    实现补救下载操作的标准接口，提供绕过 TMD 直接下载媒体文件的功能。

    **架构说明**:
    此服务通过 IProgressCallback 报告进度，不直接产生 UI 输出。
    进度报告由调用方（菜单/CLI）通过回调实现。

    Attributes:
        config: 配置实例
        logger: 日志实例
        download_service: 下载服务实例（可选）
        database_service: 数据库服务实例（可选）

    Example:
        >>> from tmdc.config.config import TMDConfig
        >>> from tmdc.services.remedy_service import RemedyService
        >>> import logging
        >>>
        >>> config = TMDConfig()
        >>> logger = logging.getLogger("TMDController")
        >>> remedy = RemedyService(config, logger)
        >>>
        >>> # 执行补救下载（使用默认进度输出）
        >>> success = remedy.execute()
        >>> print(f"补救下载{'成功' if success else '失败'}")
    """

    def __init__(
        self,
        config: "IConfig",
        logger: "ILogger",
        download_service: Optional["IDownloadService"] = None,
        database_service: Optional["IDatabaseService"] = None,
    ) -> None:
        """
        初始化补救服务

        Args:
            config: 配置实例
            logger: 日志实例
            download_service: 下载服务实例（可选）
            database_service: 数据库服务实例（可选）
        """
        self.config = config
        self.logger = logger
        self.download_service = download_service
        self.database_service = database_service

    # ==================== 公共接口方法 ====================

    def execute(
        self,
        progress_callback: Optional["IProgressCallback"] = None,
    ) -> bool:
        """
        执行补救下载

        从 errors.json 读取失败任务，直接下载媒体文件（绕过 TMD）。

        Args:
            progress_callback: 进度回调接口，用于报告进度。
                              如果为 None，则使用默认的 print 输出。

        Returns:
            操作是否成功
        """
        requests = _get_requests()
        if not requests:
            error_msg = "此功能需要 requests 库，请运行: pip install requests"
            self.logger.error(error_msg)
            if progress_callback:
                progress_callback.on_complete(0, 0)
            else:
                print(f"❌ {error_msg}")
            return False

        errors_path = (
            Path(self.config.root_path) / ".data" / "errors.json" if self.config.root_path else None
        )
        if not errors_path or not errors_path.exists():
            msg = "没有需要下载的任务（errors.json 不存在）"
            self.logger.info(msg)
            if progress_callback:
                progress_callback.on_start(0, msg)
                progress_callback.on_complete(0, 0)
            else:
                print(f"📝 {msg}")
            return False

        try:
            with open(errors_path, "r", encoding="utf-8") as f:
                errors_data = json.load(f)
        except Exception as e:
            error_msg = f"读取 errors.json 失败: {e}"
            self.logger.error(error_msg)
            if progress_callback:
                progress_callback.on_complete(0, 0)
            else:
                print(f"❌ {error_msg}")
            return False

        total_tweets = sum(len(tweets) for tweets in errors_data.values())
        if total_tweets == 0:
            msg = "没有需要下载的任务（errors.json 为空）"
            self.logger.info(msg)
            if progress_callback:
                progress_callback.on_start(0, msg)
                progress_callback.on_complete(0, 0)
            else:
                print(f"📝 {msg}")
            return False

        start_msg = f"发现 {total_tweets} 个失败推文待处理"
        if progress_callback:
            progress_callback.on_start(total_tweets, start_msg)
        else:
            print("\n⚠️  补救下载模式（绕开TMD）")
            print(f"📝 {start_msg}")
            print("💡 此功能绕过 TMD 核心，直接下载媒体文件")
            print("   适用于 TMD 多次恢复仍无法完成的顽固任务\n")

        session = self._create_remedy_session()
        success_count, fail_count = self._do_remedy_download(
            errors_data, errors_path, session, progress_callback
        )

        if progress_callback:
            progress_callback.on_complete(success_count, fail_count)
        else:
            print(f"\n📊 下载完成：成功 {success_count}，失败 {fail_count}")
            if fail_count == 0:
                print("✅ 所有失败推文已成功下载！")
            else:
                print(f"📝 仍有 {fail_count} 个推文无法下载")

        return fail_count == 0

    def get_failed_tasks(self) -> List[Dict[str, Any]]:
        """
        获取失败任务列表

        从 errors.json 读取失败任务信息。

        Returns:
            失败任务信息列表
        """
        if not self.config.root_path:
            return []
        errors_path = Path(self.config.root_path) / ".data" / "errors.json"
        if not errors_path.exists():
            return []

        try:
            with open(errors_path, "r", encoding="utf-8") as f:
                errors_data = json.load(f)

            tasks = []
            for entity_id, tweets in errors_data.items():
                for tweet in tweets:
                    tweet_id = tweet.get("Id", tweet.get("id", 0))
                    urls = tweet.get("Urls", [])
                    text = tweet.get("Text", "")
                    creator = tweet.get("Creator", {})
                    created_at = tweet.get("CreatedAt", "")

                    tasks.append(
                        {
                            "entity_id": entity_id,
                            "tweet_id": tweet_id,
                            "urls": urls,
                            "text": text,
                            "creator": creator,
                            "created_at": created_at,
                        }
                    )

            return tasks
        except Exception:
            return []

    # ==================== 内部方法 ====================

    def _create_remedy_session(self) -> Any:
        """
        创建 requests 会话（支持代理配置）

        Returns:
            requests.Session 实例
        """
        requests = _get_requests()
        if not requests:
            raise RuntimeError("requests 模块未安装")
        session = requests.Session()
        session.headers.update(
            {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
        # 配置代理（如果启用）
        if self.config.use_proxy:
            proxies = {
                "http": f"http://{self.config.proxy_hostname}:{self.config.proxy_tcp_port}",
                "https": f"http://{self.config.proxy_hostname}:{self.config.proxy_tcp_port}",
            }
            session.proxies.update(proxies)
        return session

    def _do_remedy_download(
        self,
        errors_data: Dict[str, Any],
        errors_path: Path,
        session: Any,
        progress_callback: Optional["IProgressCallback"] = None,
    ) -> Tuple[int, int]:
        """
        执行补救下载（精确到每个URL），优化数据库连接复用

        Args:
            errors_data: 错误数据字典
            errors_path: errors.json 文件路径
            session: requests 会话
            progress_callback: 进度回调接口

        Returns:
            (成功数量, 失败数量)
        """
        success_count = 0
        fail_count = 0
        remaining: Dict[str, List[Dict[str, Any]]] = {}

        if not self.config.root_path:
            return success_count, fail_count

        db_path = Path(self.config.root_path) / ".data" / "foo.db"
        users_dir = Path(self.config.root_path) / "users"

        # 预加载所有用户目录信息，避免重复查询数据库
        entity_dirs = self._preload_entity_dirs(db_path, errors_data.keys())

        current = 0
        total = sum(len(tweets) for tweets in errors_data.values())

        for entity_id, tweets in errors_data.items():
            for tweet in tweets:
                current += 1
                tweet_id = tweet.get("Id", tweet.get("id", 0))
                urls = tweet.get("Urls", [])
                text = tweet.get("Text", "")
                creator = tweet.get("Creator", {})
                created_at = tweet.get("CreatedAt", "")

                if not urls:
                    continue

                # 从预加载的缓存中获取用户目录
                user_dir = entity_dirs.get(int(entity_id))

                # 缓存未命中时尝试从目录名匹配
                if not user_dir:
                    screen_name = creator.get("ScreenName", "") if creator else ""
                    if screen_name:
                        for d in users_dir.iterdir() if users_dir.exists() else []:
                            if f"({screen_name})" in d.name:
                                user_dir = d
                                break

                if not user_dir:
                    error_msg = f"推文 {tweet_id}: 无法找到用户目录"
                    self.logger.warning(error_msg)
                    fail_count += len(urls)
                    if entity_id not in remaining:
                        remaining[entity_id] = []
                    remaining[entity_id].append(tweet)
                    if progress_callback:
                        progress_callback.on_item_failed(str(tweet_id), error_msg)
                    else:
                        print(f"  ⚠️  {error_msg}")
                    continue

                progress_msg = f"推文 {tweet_id}: {text[:50]}..."
                if progress_callback:
                    progress_callback.on_progress(current, progress_msg)
                else:
                    print(f"  📥 {progress_msg}")

                downloaded_files: List[Path] = []
                failed_urls: List[str] = []

                for url in urls:
                    filepath = self._remedy_download_file(
                        url, user_dir, session, text, progress_callback
                    )
                    if filepath:
                        success_count += 1
                        downloaded_files.append(filepath)
                    else:
                        fail_count += 1
                        failed_urls.append(url)

                if downloaded_files:
                    self._set_file_timestamps(downloaded_files, created_at)

                if failed_urls:
                    tweet_copy = tweet.copy()
                    tweet_copy["Urls"] = failed_urls
                    if entity_id not in remaining:
                        remaining[entity_id] = []
                    remaining[entity_id].append(tweet_copy)

        if remaining:
            with open(errors_path, "w", encoding="utf-8") as f:
                json.dump(remaining, f, indent=2)
        else:
            errors_path.unlink(missing_ok=True)

        return success_count, fail_count

    def _preload_entity_dirs(self, db_path: Path, entity_ids: Any) -> Dict[int, Path]:
        """
        预加载所有实体ID对应的用户目录，减少数据库连接次数

        Args:
            db_path: 数据库文件路径
            entity_ids: 实体 ID 集合

        Returns:
            实体 ID 到目录路径的映射字典
        """
        entity_dirs: Dict[int, Path] = {}
        if not db_path.exists():
            return entity_dirs

        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # 一次性查询所有需要的实体
            ids_tuple = tuple(int(eid) for eid in entity_ids)
            if len(ids_tuple) == 1:
                cursor.execute(
                    "SELECT id, parent_dir, name FROM user_entities WHERE id=?",
                    ids_tuple,
                )
            else:
                cursor.execute(
                    f"SELECT id, parent_dir, name FROM user_entities WHERE id IN ({','.join('?' * len(ids_tuple))})",
                    ids_tuple,
                )

            for row in cursor.fetchall():
                eid, parent_dir, name = row
                parent_path = Path(parent_dir)
                if not parent_path.is_absolute():
                    if not self.config.root_path:
                        continue
                    parent_path = Path(self.config.root_path) / parent_dir
                entity_dirs[eid] = parent_path / name

            conn.close()
        except Exception as e:
            self.logger.warning(f"预加载实体目录失败: {e}")

        return entity_dirs

    def _remedy_download_file(
        self,
        url: str,
        save_dir: Path,
        session: Any,
        tweet_text: str,
        progress_callback: Optional["IProgressCallback"] = None,
    ) -> Optional[Path]:
        """
        下载单个文件（参考TMD方式）

        Args:
            url: 文件 URL
            save_dir: 保存目录
            session: requests 会话
            tweet_text: 推文文本
            progress_callback: 进度回调接口

        Returns:
            下载成功的文件路径，如果失败则返回 None
        """
        from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

        # 高清图片请求参数：添加 name=4096x4096 获取最高质量图片
        parsed_url = urlparse(url)
        params = dict(parse_qsl(parsed_url.query)) if parsed_url.query else {}
        params["name"] = "4096x4096"
        new_query = urlencode(params)
        hd_url = urlunparse(parsed_url._replace(query=new_query))

        filename = None
        filepath = None

        for attempt in range(C.REMEDY_RETRY):
            try:
                resp = session.get(hd_url, timeout=C.REMEDY_TIMEOUT, stream=True)
                resp.raise_for_status()

                content_length = resp.headers.get("content-length")
                if content_length and int(content_length) > C.REMEDY_MAX_SIZE_MB * 1024 * 1024:
                    error_msg = "文件过大"
                    if progress_callback:
                        progress_callback.on_item_failed(url, error_msg)
                    else:
                        print(f"      ✗ {error_msg}")
                    return None

                ext = get_ext_from_url(url)
                filename = generate_filename_from_text(tweet_text, ext)

                save_dir.mkdir(parents=True, exist_ok=True)

                filepath = unique_path(save_dir / filename)

                with open(filepath, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

                success_msg = filepath.name
                if progress_callback:
                    progress_callback.on_item_success(url, success_msg)
                else:
                    print(f"      ✓ {success_msg}")
                return filepath

            except Exception as e:
                if attempt < C.REMEDY_RETRY - 1:
                    time.sleep(1)
                else:
                    error_msg = str(e)
                    if "No such file or directory" in error_msg or "Invalid argument" in error_msg:
                        detail = f"文件名错误: {error_msg[:60]}"
                        if progress_callback:
                            progress_callback.on_item_failed(url, detail)
                        else:
                            print(f"      ✗ {detail}")
                            print(f"        保存目录: {save_dir}")
                            print(f"        原始文件名: {filename if 'filename' in dir() else 'N/A'}")
                            print(f"        完整路径: {filepath if 'filepath' in dir() else 'N/A'}")
                    else:
                        if progress_callback:
                            progress_callback.on_item_failed(url, error_msg[:40])
                        else:
                            print(f"      ✗ {error_msg[:40]}")
        return None

    def _set_file_timestamps(self, filepaths: List[Path], created_at_str: str) -> None:
        """
        设置文件时间戳（与 TMD Go 保持一致）

        Go 实现: os.Chtimes(path, time.Time{}, tweet.CreatedAt)
        - 访问时间 (atime): 0 (time.Time{} 零值)
        - 修改时间 (mtime): 推文创建时间

        Args:
            filepaths: 文件路径列表
            created_at_str: 创建时间字符串
        """
        if not created_at_str:
            return

        try:
            dt = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
            mtime = dt.timestamp()
            atime = 0  # 访问时间设为 0，与 Go 的 time.Time{} 一致

            for filepath in filepaths:
                try:
                    os.utime(filepath, (atime, mtime))
                except Exception:
                    pass
        except Exception:
            pass


__all__ = ["RemedyService"]
