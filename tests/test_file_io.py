# -*- coding: utf-8 -*-
"""测试 file_io.py"""

import pytest
import tempfile
import os
from pathlib import Path
from datetime import datetime

from tmdc.utils.file_io import (
    atomic_write_yaml,
    backup_foo_db,
    ensure_dir,
    read_file_lines,
    get_file_size,
    get_errors_json_path,
)


class TestAtomicWriteYaml:
    """原子写入 YAML 测试"""

    def test_write_dict(self):
        """测试写入字典"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.yaml"
            data = {"key": "value", "number": 123}
            result = atomic_write_yaml(filepath, data)
            assert result is True
            assert filepath.exists()

    def test_write_list(self):
        """测试写入列表"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.yaml"
            data = ["item1", "item2", "item3"]
            result = atomic_write_yaml(filepath, data)
            assert result is True

    def test_create_parent_dirs(self):
        """测试创建父目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "subdir" / "nested" / "test.yaml"
            data = {"key": "value"}
            result = atomic_write_yaml(filepath, data)
            assert result is True
            assert filepath.exists()

    def test_overwrite_existing(self):
        """测试覆盖现有文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.yaml"
            atomic_write_yaml(filepath, {"old": "data"})
            result = atomic_write_yaml(filepath, {"new": "data"})
            assert result is True

    def test_unicode_content(self):
        """测试 Unicode 内容"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.yaml"
            data = {"中文": "测试", "emoji": "🎉"}
            result = atomic_write_yaml(filepath, data)
            assert result is True


class TestBackupFooDb:
    """数据库备份测试"""

    def test_backup_creates_file(self):
        """测试备份创建文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "foo.db"
            db_path.write_text("test data")
            result = backup_foo_db(db_path, max_backups=5)
            assert result is True
            backup_dir = Path(tmpdir) / "backups"
            assert backup_dir.exists()
            backups = list(backup_dir.glob("foo_*.db"))
            assert len(backups) == 1

    def test_backup_nonexistent_file(self):
        """测试备份不存在的文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "nonexistent.db"
            result = backup_foo_db(db_path)
            assert result is False

    def test_max_backups_limit(self):
        """测试最大备份数限制"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "foo.db"
            db_path.write_text("test data")
            for _ in range(5):
                backup_foo_db(db_path, max_backups=3)
                import time
                time.sleep(0.01)
            backup_dir = Path(tmpdir) / "backups"
            backups = list(backup_dir.glob("foo_*.db"))
            assert len(backups) <= 3


class TestEnsureDir:
    """目录创建测试"""

    def test_create_single_dir(self):
        """测试创建单层目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = Path(tmpdir) / "newdir"
            result = ensure_dir(new_dir)
            assert result.exists()
            assert result.is_dir()

    def test_create_nested_dirs(self):
        """测试创建嵌套目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = Path(tmpdir) / "a" / "b" / "c"
            result = ensure_dir(new_dir)
            assert result.exists()

    def test_existing_dir(self):
        """测试已存在的目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = ensure_dir(tmpdir)
            assert result.exists()

    def test_string_path(self):
        """测试字符串路径"""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = os.path.join(tmpdir, "newdir")
            result = ensure_dir(new_dir)
            assert result.exists()


class TestReadFileLines:
    """文件行读取测试"""

    def test_basic_read(self):
        """测试基本读取"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("line1\nline2\nline3\n")
            temp_path = f.name
        try:
            lines = read_file_lines(temp_path)
            assert lines == ["line1", "line2", "line3"]
        finally:
            os.unlink(temp_path)

    def test_skip_empty_lines(self):
        """测试跳过空行"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("line1\n\nline2\n\n\nline3\n")
            temp_path = f.name
        try:
            lines = read_file_lines(temp_path)
            assert lines == ["line1", "line2", "line3"]
        finally:
            os.unlink(temp_path)

    def test_keep_empty_lines(self):
        """测试保留空行"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("line1\n\nline2\n")
            temp_path = f.name
        try:
            lines = read_file_lines(temp_path, skip_empty=False)
            assert "" in lines
        finally:
            os.unlink(temp_path)

    def test_no_strip(self):
        """测试不去除空白"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("  line1  \n\tline2\t\n")
            temp_path = f.name
        try:
            lines = read_file_lines(temp_path, strip_lines=False)
            assert "  line1  \n" in lines or "  line1  " in lines
        finally:
            os.unlink(temp_path)

    def test_file_not_found(self):
        """测试文件不存在"""
        with pytest.raises(FileNotFoundError):
            read_file_lines("/nonexistent/path/file.txt")


class TestGetFileSize:
    """文件大小获取测试"""

    def test_existing_file(self):
        """测试已存在的文件"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Hello, World!")
            temp_path = f.name
        try:
            size = get_file_size(temp_path)
            assert size == 13
        finally:
            os.unlink(temp_path)

    def test_nonexistent_file(self):
        """测试不存在的文件"""
        size = get_file_size("/nonexistent/path/file.txt")
        assert size == 0

    def test_empty_file(self):
        """测试空文件"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            temp_path = f.name
        try:
            size = get_file_size(temp_path)
            assert size == 0
        finally:
            os.unlink(temp_path)

    def test_path_object(self):
        """测试 Path 对象"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("test")
            temp_path = Path(f.name)
        try:
            size = get_file_size(temp_path)
            assert size == 4
        finally:
            temp_path.unlink()


class TestGetErrorsJsonPath:
    """errors.json 路径获取测试"""

    def test_valid_root_path(self):
        """测试有效的根路径"""
        result = get_errors_json_path("/path/to/downloads")
        expected = Path("/path/to/downloads") / ".data" / "errors.json"
        assert result == expected

    def test_none_root_path(self):
        """测试 None 根路径"""
        result = get_errors_json_path(None)
        assert result is None

    def test_empty_root_path(self):
        """测试空根路径"""
        result = get_errors_json_path("")
        assert result is None
