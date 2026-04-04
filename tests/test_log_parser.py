# -*- coding: utf-8 -*-
"""测试 log_parser.py"""

import pytest
import tempfile
import os
from pathlib import Path

from tmdc.parsers.log_parser import TMDLogParser
from tmdc.tmd_types import DownloadResult


class TestDownloadResult:
    """下载结果数据类测试"""

    def test_default_values(self):
        """测试默认值"""
        result = DownloadResult()
        assert result.exit_code == 0
        assert result.warn_count == 0
        assert result.error_count == 0
        assert result.warn_users == []
        assert result.error_messages == []
        assert result.raw_output == ""
        assert result.duration == 0.0
        assert result.target_type == ""
        assert result.target_id == ""

    def test_custom_values(self):
        """测试自定义值"""
        result = DownloadResult(
            exit_code=1,
            warn_count=5,
            error_count=3,
            warn_users=["user1", "user2"],
            error_messages=["error1", "error2", "error3"],
            raw_output="test output",
            duration=1.5,
            target_type="user",
            target_id="elonmusk",
        )
        assert result.exit_code == 1
        assert result.warn_count == 5
        assert result.error_count == 3
        assert len(result.warn_users) == 2
        assert len(result.error_messages) == 3
        assert result.raw_output == "test output"
        assert result.duration == 1.5
        assert result.target_type == "user"
        assert result.target_id == "elonmusk"


class TestTMDLogParser:
    """日志解析器测试"""

    def test_parse_empty_file(self):
        """测试空文件"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("")
            log_path = Path(f.name)

        try:
            parser = TMDLogParser(log_path)
            content = parser.read_increment(0)
            result = parser.parse(content)
            assert result.exit_code == 0
        finally:
            log_path.unlink()

    def test_parse_success_log(self):
        """测试成功日志"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("Download completed successfully\n")
            log_path = Path(f.name)

        try:
            parser = TMDLogParser(log_path)
            content = parser.read_increment(0)
            result = parser.parse(content)
            assert result.exit_code == 0
        finally:
            log_path.unlink()

    def test_parse_warn_log(self):
        """测试警告日志"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("failed to get user medias user=testuser\n")
            log_path = Path(f.name)

        try:
            parser = TMDLogParser(log_path)
            content = parser.read_increment(0)
            result = parser.parse(content)
            assert result.warn_count == 1
            assert "testuser" in result.warn_users
        finally:
            log_path.unlink()

    def test_parse_warn_log_old_format(self):
        """测试旧格式警告日志"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write('failed to get user medias user="Test User(testuser)"\n')
            log_path = Path(f.name)

        try:
            parser = TMDLogParser(log_path)
            content = parser.read_increment(0)
            result = parser.parse(content)
            assert result.warn_count == 1
            assert "testuser" in result.warn_users
        finally:
            log_path.unlink()

    def test_parse_error_log(self):
        """测试错误日志"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("ERROR[2024-01-15] Connection failed\n")
            log_path = Path(f.name)

        try:
            parser = TMDLogParser(log_path)
            content = parser.read_increment(0)
            result = parser.parse(content)
            assert result.error_count == 1
            assert len(result.error_messages) == 1
        finally:
            log_path.unlink()

    def test_parse_fatal_log(self):
        """测试致命错误日志"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("FATA[2024-01-15] Critical error occurred\n")
            log_path = Path(f.name)

        try:
            parser = TMDLogParser(log_path)
            content = parser.read_increment(0)
            result = parser.parse(content)
            assert result.error_count == 1
        finally:
            log_path.unlink()

    def test_parse_multiple_warnings(self):
        """测试多个警告"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("failed to get user medias user=user1\n")
            f.write("failed to get user medias user=user2\n")
            f.write("failed to get user medias user=user1\n")
            log_path = Path(f.name)

        try:
            parser = TMDLogParser(log_path)
            content = parser.read_increment(0)
            result = parser.parse(content)
            assert result.warn_count == 2
            assert "user1" in result.warn_users
            assert "user2" in result.warn_users
        finally:
            log_path.unlink()

    def test_nonexistent_file(self):
        """测试不存在的文件"""
        parser = TMDLogParser(Path("/nonexistent/path.log"))
        assert parser.last_error is None
        assert parser.get_size() == 0
        content = parser.read_increment(0)
        assert content == ""

    def test_get_size(self):
        """测试获取文件大小"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("test content\n")
            log_path = Path(f.name)

        try:
            parser = TMDLogParser(log_path)
            size = parser.get_size()
            assert size > 0
        finally:
            log_path.unlink()

    def test_get_tail(self):
        """测试获取尾部"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            for i in range(20):
                f.write(f"Line {i}\n")
            log_path = Path(f.name)

        try:
            parser = TMDLogParser(log_path)
            tail = parser.get_tail(10)
            lines = tail.strip().split("\n")
            assert len(lines) == 10
            assert "Line 19" in tail
        finally:
            log_path.unlink()

    def test_get_tail_nonexistent(self):
        """测试获取不存在文件的尾部"""
        parser = TMDLogParser(Path("/nonexistent/path.log"))
        tail = parser.get_tail(10)
        assert tail == ""

    def test_parse_increment(self):
        """测试增量解析"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("Initial content\n")
            initial_size = f.tell()
            f.write("Additional content\n")
            log_path = Path(f.name)

        try:
            parser = TMDLogParser(log_path)
            result = parser.parse_increment(initial_size)
            assert "Additional content" in result.raw_output
        finally:
            log_path.unlink()

    def test_clear_log(self):
        """测试清空日志"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("Content to be cleared\n")
            log_path = Path(f.name)

        try:
            parser = TMDLogParser(log_path)
            success = parser.clear()
            assert success is True
            assert log_path.stat().st_size == 0
        finally:
            log_path.unlink()

    def test_clear_nonexistent_file(self):
        """测试清空不存在的文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "new.log"
            parser = TMDLogParser(log_path)
            success = parser.clear()
            assert success is True
            assert log_path.exists()

    def test_last_error_tracking(self):
        """测试错误追踪"""
        parser = TMDLogParser(Path("/nonexistent/path.log"))
        parser.read_increment(0)
        parser.get_tail(10)
