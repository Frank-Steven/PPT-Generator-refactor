"""工具函数单元测试。

本文件测试路径处理相关的工具函数。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ppt_generator.core.exceptions import MissingFileError


class TestPathHandling:
    """测试路径处理功能。"""

    def test_validate_existing_path(self, tmp_path: Path) -> None:
        """测试验证存在的路径。"""
        existing_file = tmp_path / "existing.txt"
        existing_file.touch()

        result = Path(str(existing_file))

        assert result == existing_file
        assert isinstance(result, Path)

    def test_ensure_dir(self, tmp_path: Path) -> None:
        """测试确保目录存在。"""
        new_dir = tmp_path / "new" / "nested" / "dir"

        new_dir.mkdir(parents=True, exist_ok=True)

        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_ensure_existing_dir(self, tmp_path: Path) -> None:
        """测试确保已存在的目录。"""
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()

        existing_dir.mkdir(parents=True, exist_ok=True)

        assert existing_dir.exists()
