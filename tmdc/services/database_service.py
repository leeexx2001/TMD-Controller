# -*- coding: utf-8 -*-
"""
数据库服务模块

提供数据库操作的标准实现。

主要功能：
- 数据库连接管理
- 用户/列表查询
- 时间戳管理
- 路径统计
"""

from __future__ import annotations

# 标准库
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Generator, List, Optional, Tuple

if TYPE_CHECKING:
    import logging

    from ..config.config import TMDConfig

# 第三方库（无）

# 本地模块
from ..utils.formatters import parse_db_timestamp
from ..utils.text_utils import escape_like_pattern


class DatabaseService:
    """数据库服务

    实现数据库操作的标准接口，包括连接管理、查询、时间戳管理等

    Attributes:
        config: 配置实例
        logger: 日志实例
    """

    def __init__(self, config: "TMDConfig", logger: "logging.Logger") -> None:
        """初始化数据库服务

        Args:
            config: 配置实例
            logger: 日志实例
        """
        self.config = config
        self.logger = logger

    # ==================== 连接管理 ====================

    def _get_db_connection(self) -> Optional[sqlite3.Connection]:
        """获取数据库连接（纯业务逻辑，无 UI 输出）

        Returns:
            sqlite3.Connection: 数据库连接，如果失败则返回 None

        Note:
            错误信息通过 logger 记录，不直接打印
        """
        db_path = self.config.db_path
        if not db_path or not db_path.exists():
            self.logger.warning("找不到数据库文件")
            return None

        try:
            conn = sqlite3.connect(str(db_path), timeout=60.0, isolation_level="IMMEDIATE")
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=60000")
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            self.logger.error(f"数据库连接失败: {e}")
            return None

    @contextmanager
    def db_session(self) -> Generator[Optional[sqlite3.Cursor], None, None]:
        """数据库连接上下文管理器

        自动管理连接的创建、提交、回滚和关闭

        Yields:
            sqlite3.Cursor: 数据库游标，如果连接失败则 yield None
        """
        conn = self._get_db_connection()
        if not conn:
            yield None
            return

        cursor = None
        try:
            cursor = conn.cursor()
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            conn.close()

    # ==================== 查询方法 ====================

    def find_users(
        self,
        keyword: str,
        *,
        limit: Optional[int] = None,
        default_limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """搜索用户

        根据关键词搜索用户，匹配用户名或显示名称

        Args:
            keyword: 搜索关键词
            limit: 返回结果数量限制（默认使用 default_limit）
            default_limit: 默认限制数量（当 limit 为 None 时使用）

        Returns:
            List[Dict[str, Any]]: 用户信息列表

        Note:
            返回的字典包含以下字段：
            - id: 用户 ID
            - screen_name: 用户名
            - name: 显示名称
            - entity_id: 实体 ID（可选）
            - latest_release_time: 最新发布时间（可选）
        """
        effective_limit = limit if limit is not None else default_limit

        with self.db_session() as cursor:
            if cursor is None:
                return []

            try:
                pattern = escape_like_pattern(keyword)

                cursor.execute(
                    """
                    SELECT DISTINCT u.id, u.screen_name, u.name,
                           ue.id as entity_id, ue.latest_release_time
                    FROM users u
                    LEFT JOIN user_entities ue ON u.id = ue.user_id
                    WHERE u.screen_name LIKE ? ESCAPE '\\' OR u.name LIKE ? ESCAPE '\\'
                    ORDER BY u.screen_name
                    LIMIT ?
                """,
                    (pattern, pattern, effective_limit),
                )
                return [dict(row) for row in cursor.fetchall()]
            except sqlite3.Error as e:
                self.logger.error(f"搜索失败: {e}")
                return []

    def find_unlinked_users(
        self,
        *,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """查询未关联列表的用户

        查询存在于 users 表但在 user_links 表中没有关联记录的用户。
        同时关联 user_entities 表获取实体 ID，便于后续操作。

        Args:
            limit: 返回结果数量限制（None 表示不限制）

        Returns:
            List[Dict[str, Any]]: 未关联用户列表，包含以下字段：
            - id: 用户 ID
            - screen_name: 用户名
            - name: 显示名称
            - entity_id: 用户实体 ID（可能为 None）
            - is_accessible: 是否可访问（0=不可访问，1=可访问）
        """
        with self.db_session() as cursor:
            if cursor is None:
                return []

            try:
                if limit is not None:
                    cursor.execute(
                        """
                        SELECT u.id, u.screen_name, u.name, ue.id as entity_id, u.is_accessible
                        FROM users u
                        LEFT JOIN user_entities ue ON u.id = ue.user_id
                        WHERE NOT EXISTS (
                            SELECT 1 FROM user_links ul WHERE ul.user_id = u.id
                        )
                        ORDER BY u.is_accessible DESC, u.screen_name
                        LIMIT ?
                        """,
                        (limit,),
                    )
                else:
                    cursor.execute("""
                        SELECT u.id, u.screen_name, u.name, ue.id as entity_id, u.is_accessible
                        FROM users u
                        LEFT JOIN user_entities ue ON u.id = ue.user_id
                        WHERE NOT EXISTS (
                            SELECT 1 FROM user_links ul WHERE ul.user_id = u.id
                        )
                        ORDER BY u.is_accessible DESC, u.screen_name
                        """)
                return [dict(row) for row in cursor.fetchall()]
            except sqlite3.Error as e:
                self.logger.error(f"查询未关联用户失败: {e}")
                return []

    # ==================== 列表操作 ====================

    def check_list_metadata_exists(self, list_id: int) -> bool:
        """检查列表元数据是否存在（lsts 表）

        Args:
            list_id: 列表 ID

        Returns:
            bool: 列表存在返回 True，否则返回 False
        """
        with self.db_session() as cursor:
            if cursor is None:
                return False

            cursor.execute("SELECT 1 FROM lsts WHERE id = ?", (list_id,))
            return cursor.fetchone() is not None

    def check_list_entity_exists(self, list_id: int) -> bool:
        """检查列表实体是否存在（lst_entities 表）

        Args:
            list_id: 列表 ID

        Returns:
            bool: 列表实体存在返回 True，否则返回 False
        """
        with self.db_session() as cursor:
            if cursor is None:
                return False

            cursor.execute("SELECT 1 FROM lst_entities WHERE lst_id = ?", (list_id,))
            return cursor.fetchone() is not None

    # ==================== 时间戳操作 ====================

    def get_user_entity_info(self, screen_name: str) -> Optional[Dict[str, Any]]:
        """获取用户实体信息

        Args:
            screen_name: 用户名

        Returns:
            用户信息字典，包含 id, screen_name, name, entity_id, latest_release_time
        """
        with self.db_session() as cursor:
            if cursor is None:
                return None

            cursor.execute(
                """
                SELECT u.id, u.screen_name, u.name, ue.id as entity_id, ue.latest_release_time
                FROM users u
                LEFT JOIN user_entities ue ON u.id = ue.user_id
                WHERE u.screen_name = ? COLLATE NOCASE
                """,
                (screen_name,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_entity_by_id(self, entity_id: int) -> Optional[Dict[str, Any]]:
        """通过实体 ID 获取实体信息

        Args:
            entity_id: 用户实体 ID

        Returns:
            实体信息字典，包含 screen_name, entity_id
        """
        with self.db_session() as cursor:
            if cursor is None:
                return None

            cursor.execute(
                """
                SELECT u.screen_name, ue.id as entity_id
                FROM user_entities ue
                JOIN users u ON ue.user_id = u.id
                WHERE ue.id = ?
                """,
                (entity_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def set_user_timestamp(
        self,
        entity_id: int,
        target_date: Optional[datetime],
    ) -> Tuple[bool, Optional[str]]:
        """直接设置用户时间戳

        Args:
            entity_id: 用户实体 ID
            target_date: 目标时间戳，None 表示重置为全量下载

        Returns:
            (是否成功, screen_name) - 成功时返回用户名，失败时返回 None
        """
        with self.db_session() as cursor:
            if cursor is None:
                return (False, None)

            try:
                cursor.execute(
                    """
                    SELECT u.screen_name
                    FROM user_entities ue
                    JOIN users u ON ue.user_id = u.id
                    WHERE ue.id = ?
                    """,
                    (entity_id,),
                )
                row = cursor.fetchone()
                if not row:
                    return (False, None)
                screen_name = row["screen_name"]

                if target_date is None:
                    cursor.execute(
                        "UPDATE user_entities SET latest_release_time = NULL WHERE id = ?",
                        (entity_id,),
                    )
                else:
                    ts_str = target_date.strftime("%Y-%m-%d %H:%M:%S")
                    cursor.execute(
                        "UPDATE user_entities SET latest_release_time = ? WHERE id = ?",
                        (ts_str, entity_id),
                    )
                return (cursor.rowcount > 0, screen_name)
            except sqlite3.Error:
                return (False, None)

    def set_list_timestamp(
        self,
        list_id: int,
        target_date: Optional[datetime],
    ) -> bool:
        """直接设置列表时间戳

        Args:
            list_id: 列表 ID
            target_date: 目标时间戳，None 表示重置为全量下载

        Returns:
            是否成功
        """
        with self.db_session() as cursor:
            if cursor is None:
                return False

            try:
                if target_date is None:
                    cursor.execute(
                        "UPDATE lst_entities SET latest_release_time = NULL WHERE lst_id = ?",
                        (list_id,),
                    )
                else:
                    ts_str = target_date.strftime("%Y-%m-%d %H:%M:%S")
                    cursor.execute(
                        "UPDATE lst_entities SET latest_release_time = ? WHERE lst_id = ?",
                        (ts_str, list_id),
                    )
                return cursor.rowcount > 0
            except sqlite3.Error:
                return False

    def find_targets(
        self,
        keyword: str,
        *,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """统一搜索用户和列表

        Args:
            keyword: 搜索关键词（用户名、列表ID）
            limit: 返回结果数量限制

        Returns:
            List[Dict[str, Any]]: 目标列表，每项包含:
                - type: "user" 或 "list"
                - id: 用户ID或列表ID
                - name: 显示名称
                - screen_name: 用户名（仅用户）
                - timestamp: 时间戳
        """
        results: List[Dict[str, Any]] = []
        keyword_stripped = (keyword or "").strip()

        if not keyword_stripped:
            return results

        with self.db_session() as cursor:
            if cursor is None:
                return results

            try:
                pattern = escape_like_pattern(keyword_stripped)

                cursor.execute(
                    """
                    SELECT DISTINCT u.id, u.screen_name, u.name,
                           ue.id as entity_id, ue.latest_release_time
                    FROM users u
                    LEFT JOIN user_entities ue ON u.id = ue.user_id
                    WHERE u.screen_name LIKE ? ESCAPE '\\' OR u.name LIKE ? ESCAPE '\\'
                    ORDER BY u.screen_name
                    LIMIT ?
                """,
                    (pattern, pattern, limit),
                )
                for row in cursor.fetchall():
                    results.append(
                        {
                            "type": "user",
                            "id": row["id"],
                            "screen_name": row["screen_name"] or "",
                            "name": row["name"] or "",
                            "entity_id": row["entity_id"],
                            "timestamp": row["latest_release_time"],
                        }
                    )

                if keyword_stripped.isdigit():
                    list_id = int(keyword_stripped)
                    cursor.execute(
                        """
                        SELECT le.lst_id, le.latest_release_time
                        FROM lst_entities le
                        WHERE le.lst_id = ?
                    """,
                        (list_id,),
                    )
                    row = cursor.fetchone()
                    if row:
                        results.append(
                            {
                                "type": "list",
                                "id": row["lst_id"],
                                "name": f"列表 {row['lst_id']}",
                                "timestamp": row["latest_release_time"],
                            }
                        )

            except sqlite3.Error as e:
                self.logger.error(f"搜索失败: {e}")

        return results

    def is_database_available(self) -> bool:
        """检查数据库是否可用

        检查数据库文件是否存在且可访问

        Returns:
            数据库可用返回 True，否则返回 False
        """
        db_path = self.config.db_path
        if not db_path or not db_path.exists():
            return False
        return True

    def get_database_unavailable_message(self) -> str:
        """获取数据库不可用时的提示消息

        Returns:
            提示消息字符串
        """
        db_path = self.config.db_path
        if not db_path:
            return "❌ 找不到 TMD 数据库，请确保已运行过至少一次下载"
        return f"❌ 找不到 TMD 数据库，请确保已运行过至少一次下载\n预期路径: {db_path}"

    # ==================== 路径统计 ====================

    def get_path_statistics(self, path: Optional[str] = None) -> Dict[str, Any]:
        """获取路径统计信息

        Args:
            path: 路径（当前未使用，保留用于未来扩展）

        Returns:
            Dict[str, Any]: 统计信息字典，包含：
            - user_count: 用户实体数量
            - user_dir_count: 用户目录数量
            - list_count: 列表实体数量
            - list_dir_count: 列表目录数量
            - success: 是否成功获取统计信息
        """
        with self.db_session() as cursor:
            if cursor is None:
                return {
                    "user_count": 0,
                    "user_dir_count": 0,
                    "list_count": 0,
                    "list_dir_count": 0,
                    "success": False,
                }

            try:
                # 统计用户实体路径
                cursor.execute("SELECT COUNT(DISTINCT parent_dir) FROM user_entities")
                user_dir_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM user_entities")
                user_count = cursor.fetchone()[0]

                # 统计列表实体路径
                cursor.execute("SELECT COUNT(DISTINCT parent_dir) FROM lst_entities")
                list_dir_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM lst_entities")
                list_count = cursor.fetchone()[0]

                return {
                    "user_count": user_count,
                    "user_dir_count": user_dir_count,
                    "list_count": list_count,
                    "list_dir_count": list_dir_count,
                    "success": True,
                }

            except sqlite3.Error as e:
                self.logger.error(f"统计路径失败: {e}")
                return {
                    "user_count": 0,
                    "user_dir_count": 0,
                    "list_count": 0,
                    "list_dir_count": 0,
                    "success": False,
                }

    # ==================== 删除操作 ====================

    def delete_user_project(self, uid: int) -> Tuple[bool, str, Dict[str, int]]:
        """删除用户项目的所有数据库记录

        级联删除以下表中的相关数据：
        - user_links: 用户-列表关联
        - user_entities: 用户下载实体
        - user_previous_names: 历史名称记录
        - users: 用户主记录

        Args:
            uid: 用户 ID（Twitter 用户唯一标识符）

        Returns:
            Tuple[bool, str, Dict[str, int]]:
                - 是否成功
                - 操作消息或错误信息
                - 各表删除行数统计 {"links": n, "entities": n, "names": n, "users": n}
        """
        stats = {"links": 0, "entities": 0, "names": 0, "users": 0}

        with self.db_session() as cursor:
            if cursor is None:
                return (False, "数据库连接失败", stats)

            try:
                cursor.execute("DELETE FROM user_links WHERE user_id = ?", (uid,))
                stats["links"] = cursor.rowcount

                cursor.execute("DELETE FROM user_entities WHERE user_id = ?", (uid,))
                stats["entities"] = cursor.rowcount

                cursor.execute("DELETE FROM user_previous_names WHERE uid = ?", (uid,))
                stats["names"] = cursor.rowcount

                cursor.execute("DELETE FROM users WHERE id = ?", (uid,))
                stats["users"] = cursor.rowcount

                total_deleted = sum(stats.values())
                if stats["users"] == 0:
                    return (False, f"用户 ID {uid} 不存在于数据库中", stats)

                return (
                    True,
                    f"已删除用户项目，共清理 {total_deleted} 条记录",
                    stats,
                )

            except sqlite3.Error as e:
                self.logger.error(f"删除用户项目失败(uid={uid}): {e}")
                return (False, f"数据库操作失败: {e}", stats)

    # ==================== 辅助方法 ====================

    def execute_transaction(self, operations: List[Tuple[str, tuple]]) -> bool:
        """执行数据库事务操作

        Args:
            operations: 操作列表，每个元素为 (sql, params) 元组

        Returns:
            bool: 是否成功

        Note:
            发生异常时会自动回滚（由 _db_session 处理）
        """
        with self.db_session() as cursor:
            if cursor is None:
                return False

            for sql, params in operations:
                cursor.execute(sql, params)

            return True


__all__ = ["DatabaseService"]
