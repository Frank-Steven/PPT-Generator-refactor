"""模板加载器单元测试。

本文件测试TemplateLoader的各种加载场景，包括：
- 加载有效模板
- 加载无效模板
- 提取布局信息
- 边界情况
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ppt_generator.core.exceptions import MissingFileError, TemplateLoadError
from ppt_generator.templates import TemplateLoader


class TestTemplateLoader:
    """测试TemplateLoader类。"""

    def test_list_layouts(self, template_loader: TemplateLoader) -> None:
        """测试列出模板中的布局。"""
        layouts = template_loader.list_layouts()

        assert len(layouts) > 0
        assert all(hasattr(layout, "name") for layout in layouts)
        assert all(hasattr(layout, "placeholders") for layout in layouts)

    def test_layout_has_placeholders(self, template_loader: TemplateLoader) -> None:
        """测试布局包含占位符信息。"""
        layouts = template_loader.list_layouts()

        for layout in layouts:
            for placeholder in layout.placeholders:
                assert placeholder.name
                assert placeholder.index >= 0
                assert placeholder.shape_id >= 0

    def test_load_nonexistent_template(self, tmp_path: Path) -> None:
        """测试加载不存在的模板文件。"""
        nonexistent_path = tmp_path / "nonexistent.pptx"

        with pytest.raises(MissingFileError):
            TemplateLoader(nonexistent_path)

    def test_load_invalid_file(self, tmp_path: Path) -> None:
        """测试加载无效文件。"""
        invalid_path = tmp_path / "invalid.pptx"
        with open(invalid_path, "w") as f:
            f.write("not a pptx file")

        with pytest.raises(TemplateLoadError):
            TemplateLoader(invalid_path)

    def test_layout_names_are_strings(self, template_loader: TemplateLoader) -> None:
        """测试布局名称都是字符串。"""
        layouts = template_loader.list_layouts()

        for layout in layouts:
            assert isinstance(layout.name, str)
            assert len(layout.name) > 0

    def test_placeholder_types(self, template_loader: TemplateLoader) -> None:
        """测试占位符类型。"""
        layouts = template_loader.list_layouts()

        for layout in layouts:
            for placeholder in layout.placeholders:
                assert isinstance(placeholder.placeholder_type, str)
