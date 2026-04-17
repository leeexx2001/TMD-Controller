# -*- coding: utf-8 -*-
"""DatabaseService 删除用户项目功能测试"""

import os
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from tmdc.services.database_service import DatabaseService
from tmdc.tmd_types import create_logger


@pytest.fixture
def temp_db():
    """创建临时测试数据库（含完整关联数据）"""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    conn = sqlite3.connect(path)
    conn.executescript("""
        PRAGMA journal_mode=WAL;
        PRAGMA foreign_keys=ON;
        CREATE TABLE users (
            id INTEGER NOT NULL PRIMARY KEY,
            screen_name VARCHAR NOT NULL UNIQUE,
            name VARCHAR NOT NULL,
            protected BOOLEAN NOT NULL DEFAULT 0,
            friends_count INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE user_previous_names (
            id INTEGER NOT NULL PRIMARY KEY,
            uid INTEGER NOT NULL,
            screen_name VARCHAR NOT NULL,
            name VARCHAR NOT NULL,
            record_date DATE NOT NULL,
            FOREIGN KEY(uid) REFERENCES users(id)
        );
        CREATE TABLE lsts (
            id INTEGER NOT NULL PRIMARY KEY,
            name VARCHAR NOT NULL,
            owner_uid INTEGER NOT NULL
        );
        CREATE TABLE lst_entities (
            id INTEGER NOT NULL PRIMARY KEY,
            lst_id INTEGER NOT NULL,
            name VARCHAR NOT NULL,
            parent_dir VARCHAR NOT NULL COLLATE NOCASE,
            UNIQUE(lst_id, parent_dir)
        );
        CREATE TABLE user_entities (
            id INTEGER NOT NULL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            name VARCHAR NOT NULL,
            latest_release_time DATETIME,
            parent_dir VARCHAR COLLATE NOCASE NOT NULL,
            media_count INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id),
            UNIQUE(user_id, parent_dir)
        );
        CREATE TABLE user_links (
            id INTEGER NOT NULL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            name VARCHAR NOT NULL,
            parent_lst_entity_id INTEGER NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(parent_lst_entity_id) REFERENCES lst_entities(id),
            UNIQUE(user_id, parent_lst_entity_id)
        );
        CREATE INDEX IF NOT EXISTS idx_user_links_user_id ON user_links (user_id);
    """)
    conn.execute(
        "INSERT INTO users VALUES(12345, 'testuser', 'Test User', 0, 100)"
    )
    conn.execute(
        "INSERT INTO user_previous_names VALUES(1, 12345, 'oldname', 'Old Name', '2024-01-01')"
    )
    conn.execute(
        "INSERT INTO user_entities VALUES(1, 12345, 'testuser', '2024-06-01 00:00:00', '/downloads', 50)"
    )
    conn.execute("INSERT INTO lsts VALUES(999, 'test_list', 12345)")
    conn.execute("INSERT INTO lst_entities VALUES(1, 999, 'list_ent', '/lists')")
    conn.execute(
        "INSERT INTO user_links VALUES(1, 12345, 'link_name', 1)"
    )
    conn.commit()
    conn.close()
    yield path
    if os.path.exists(path):
        os.unlink(path)


class TestDeleteUserProject:
    """删除用户项目测试类"""

    def _make_service(self, db_path):
        """辅助：创建 DatabaseService 实例"""
        config = MagicMock()
        config.db_path = Path(db_path)
        logger = create_logger("test")
        return DatabaseService(config, logger)

    def test_delete_all_related_records(self, temp_db):
        """测试删除用户时级联删除所有关联记录"""
        svc = self._make_service(temp_db)
        success, msg, stats = svc.delete_user_project(12345)

        assert success is True
        assert stats["users"] == 1
        assert stats["entities"] == 1
        assert stats["names"] == 1
        assert stats["links"] == 1

        conn = sqlite3.connect(temp_db)
        assert conn.execute("SELECT COUNT(*) FROM users WHERE id=12345").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM user_entities WHERE user_id=12345").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM user_previous_names WHERE uid=12345").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM user_links WHERE user_id=12345").fetchone()[0] == 0
        conn.close()

    def test_delete_nonexistent_user(self, temp_db):
        """测试删除不存在的用户"""
        svc = self._make_service(temp_db)
        success, msg, stats = svc.delete_user_project(99999)

        assert success is False
        assert stats["users"] == 0
        assert "不存在" in msg

    def test_delete_partial_data_user(self, temp_db):
        """测试只有用户主记录、无其他关联数据的删除"""
        conn = sqlite3.connect(temp_db)
        conn.execute("INSERT INTO users VALUES(55555, 'minimal', 'Minimal User', 0, 10)")
        conn.commit()
        conn.close()

        svc = self._make_service(temp_db)
        success, msg, stats = svc.delete_user_project(55555)

        assert success is True
        assert stats["users"] == 1
        assert stats["entities"] == 0
        assert stats["names"] == 0
        assert stats["links"] == 0

        conn = sqlite3.connect(temp_db)
        assert conn.execute("SELECT COUNT(*) FROM users WHERE id=55555").fetchone()[0] == 0
        conn.close()

    def test_delete_does_not_affect_other_users(self, temp_db):
        """测试删除一个用户不影响其他用户数据"""
        conn = sqlite3.connect(temp_db)
        conn.execute("INSERT INTO users VALUES(77777, 'otheruser', 'Other User', 1, 200)")
        conn.execute(
            "INSERT INTO user_entities VALUES(2, 77777, 'otheruser', NULL, '/downloads', 0)"
        )
        conn.commit()
        conn.close()

        svc = self._make_service(temp_db)
        success, msg, stats = svc.delete_user_project(12345)

        assert success is True

        conn = sqlite3.connect(temp_db)
        assert conn.execute("SELECT COUNT(*) FROM users WHERE id=77777").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM user_entities WHERE user_id=77777").fetchone()[0] == 1
        conn.close()

    def test_delete_with_multiple_entities_and_links(self, temp_db):
        """测试用户有多个实体和链接时的删除"""
        conn = sqlite3.connect(temp_db)
        conn.execute(
            "INSERT INTO user_entities VALUES(2, 12345, 'testuser_alt', '2024-07-01', '/alt_downloads', 20)"
        )
        conn.execute("INSERT INTO lst_entities VALUES(2, 888, 'another_list', '/lists2')")
        conn.execute(
            "INSERT INTO user_links VALUES(2, 12345, 'link_alt', 2)"
        )
        conn.commit()
        conn.close()

        svc = self._make_service(temp_db)
        success, msg, stats = svc.delete_user_project(12345)

        assert success is True
        assert stats["entities"] == 2
        assert stats["links"] == 2
        assert stats["names"] == 1
        assert stats["users"] == 1

    def test_return_value_structure(self, temp_db):
        """测试返回值结构符合约定"""
        svc = self._make_service(temp_db)
        result = svc.delete_user_project(12345)

        assert isinstance(result, tuple)
        assert len(result) == 3
        success, message, stats = result
        assert isinstance(success, bool)
        assert isinstance(message, str)
        assert isinstance(stats, dict)
        assert set(stats.keys()) == {"links", "entities", "names", "users"}
