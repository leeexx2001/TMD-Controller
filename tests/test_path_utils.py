# -*- coding: utf-8 -*-
"""测试 path_utils.py"""

import pytest
import tempfile
from pathlib import Path

from tmdc.utils.path_utils import (
    sanitize_win_filename,
    unique_path,
    get_ext_from_url,
    generate_filename_from_text,
    normalize_path,
)


class TestSanitizeWinFilename:
    """Windows 文件名清理测试"""

    def test_remove_invalid_chars(self):
        """测试移除非法字符"""
        assert sanitize_win_filename("test<file>.txt") == "testfile.txt"
        assert sanitize_win_filename('test"file|.txt') == "testfile.txt"

    def test_remove_url(self):
        """测试移除 URL"""
        assert sanitize_win_filename("https://example.com/page") == "untitled"

    def test_reserved_name(self):
        """测试保留名称"""
        assert sanitize_win_filename("CON") == "CON_"
        assert sanitize_win_filename("NUL") == "NUL_"
        assert sanitize_win_filename("PRN") == "PRN_"

    def test_newline_handling(self):
        """测试换行符处理"""
        assert sanitize_win_filename("test\rfile") == "testfile"
        assert sanitize_win_filename("test\nfile") == "test file"

    def test_max_bytes(self):
        """测试字节限制"""
        long_name = "a" * 300
        result = sanitize_win_filename(long_name, max_bytes=100)
        assert len(result.encode("utf-8")) <= 100

    def test_unicode_chars(self):
        """测试 Unicode 字符"""
        result = sanitize_win_filename("测试文件.txt")
        assert "测试文件" in result

    def test_strip_dots_and_spaces(self):
        """测试去除首尾点和空格"""
        assert sanitize_win_filename("  test.txt  ") == "test.txt"
        assert sanitize_win_filename("...test.txt...") == "test.txt"

    def test_empty_result(self):
        """测试空结果"""
        assert sanitize_win_filename("") == "untitled"
        assert sanitize_win_filename("   ") == "untitled"


class TestUniquePath:
    """唯一路径生成测试"""

    def test_nonexistent_file(self):
        """测试不存在的文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "test.txt"
            result = unique_path(p)
            assert result == p

    def test_existing_file(self):
        """测试已存在的文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "test.txt"
            p.touch()
            result = unique_path(p)
            assert result.name == "test(1).txt"

    def test_multiple_existing(self):
        """测试多个已存在文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            p1 = Path(tmpdir) / "test.txt"
            p2 = Path(tmpdir) / "test(1).txt"
            p1.touch()
            p2.touch()
            result = unique_path(p1)
            assert result.name == "test(2).txt"

    def test_no_extension(self):
        """测试无扩展名"""
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "testfile"
            p.touch()
            result = unique_path(p)
            assert result.name == "testfile(1)"


class TestGetExtFromUrl:
    """从 URL 获取扩展名测试"""

    def test_normal_url(self):
        """测试正常 URL"""
        assert get_ext_from_url("https://example.com/image.jpg") == ".jpg"
        assert get_ext_from_url("https://example.com/video.mp4") == ".mp4"

    def test_no_extension(self):
        """测试无扩展名"""
        assert get_ext_from_url("https://example.com/video") == ".bin"

    def test_with_query(self):
        """测试带查询参数"""
        assert get_ext_from_url("https://example.com/file.mp4?query=1") == ".mp4"

    def test_with_fragment(self):
        """测试带片段"""
        assert get_ext_from_url("https://example.com/doc.pdf#page=1") == ".pdf"

    def test_uppercase_extension(self):
        """测试大写扩展名"""
        assert get_ext_from_url("https://example.com/IMAGE.JPG") == ".jpg"

    def test_multiple_dots(self):
        """测试多个点"""
        assert get_ext_from_url("https://example.com/file.tar.gz") == ".gz"


class TestGenerateFilenameFromText:
    """从文本生成文件名测试"""

    def test_normal_text(self):
        """测试正常文本"""
        result = generate_filename_from_text("Hello World", ".txt")
        assert result == "Hello World.txt"

    def test_empty_text(self):
        """测试空文本"""
        assert generate_filename_from_text("", ".txt") == "untitled.txt"

    def test_invalid_text(self):
        """测试无效文本"""
        assert generate_filename_from_text("https://invalid.com", ".txt") == "untitled.txt"

    def test_no_extension(self):
        """测试无扩展名"""
        result = generate_filename_from_text("test", "")
        assert result == "test"


class TestNormalizePath:
    """路径标准化测试"""

    def test_forward_slash(self):
        """测试正斜杠"""
        assert normalize_path("D:/Downloads/twitter") == "D:\\Downloads\\twitter"

    def test_mixed_slashes(self):
        """测试混合斜杠"""
        assert normalize_path("D:/Downloads\\twitter") == "D:\\Downloads\\twitter"

    def test_no_slashes(self):
        """测试无斜杠"""
        assert normalize_path("filename") == "filename"

    def test_empty_string(self):
        """测试空字符串"""
        assert normalize_path("") == ""
