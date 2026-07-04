"""布局匹配器单元测试。

本文件测试LayoutMatcher的各种匹配场景，包括：
- 布局提示匹配（返回Maybe）
- 无布局提示返回Nothing
- 布局列表为空返回Nothing
- 边界情况
"""

from __future__ import annotations

import pytest
from returns.maybe import Nothing

from ppt_generator.core.models import SlideItem, SlideItemType, SlideSpec
from ppt_generator.matching import LayoutMatcher


class TestLayoutMatcher:
    """测试LayoutMatcher类。"""

    def test_select_layout_with_hint(self, sample_layouts: list) -> None:
        """测试使用布局提示选择布局。"""
        matcher = LayoutMatcher()
        slide_spec = SlideSpec(title="测试", items=[], layout_hint="Title Slide")

        selected = matcher.select_layout(slide_spec, sample_layouts)

        assert selected is not Nothing
        assert selected.unwrap().name == "Title Slide"

    def test_select_layout_with_partial_hint(self, sample_layouts: list) -> None:
        """测试使用部分布局提示选择布局。"""
        matcher = LayoutMatcher()
        slide_spec = SlideSpec(title="测试", items=[], layout_hint="Content")

        selected = matcher.select_layout(slide_spec, sample_layouts)

        assert selected is not Nothing
        assert selected.unwrap().name == "Title and Content"

    def test_select_layout_without_hint(self, sample_layouts: list) -> None:
        """测试无布局提示时返回默认布局。"""
        matcher = LayoutMatcher()
        slide_spec = SlideSpec(title="测试", items=[], layout_hint=None)

        selected = matcher.select_layout(slide_spec, sample_layouts)

        assert selected is not Nothing
        assert selected.unwrap().name == "Title and Content"

    def test_select_layout_hint_not_found(self, sample_layouts: list) -> None:
        """测试布局提示未找到时返回默认布局。"""
        matcher = LayoutMatcher()
        slide_spec = SlideSpec(title="测试", items=[], layout_hint="不存在的布局")

        selected = matcher.select_layout(slide_spec, sample_layouts)

        assert selected is not Nothing
        assert selected.unwrap().name == "Title and Content"

    def test_select_layout_empty_list(self) -> None:
        """测试布局列表为空时返回Nothing。"""
        matcher = LayoutMatcher()
        slide_spec = SlideSpec(title="测试", items=[])

        selected = matcher.select_layout(slide_spec, [])

        assert selected is Nothing

    def test_select_layout_case_insensitive(self, sample_layouts: list) -> None:
        """测试布局名称匹配不区分大小写。"""
        matcher = LayoutMatcher()
        slide_spec = SlideSpec(title="测试", items=[], layout_hint="title slide")

        selected = matcher.select_layout(slide_spec, sample_layouts)

        assert selected is not Nothing
        assert selected.unwrap().name == "Title Slide"

    def test_select_layout_with_items(self, sample_layouts: list) -> None:
        """测试包含内容项的幻灯片匹配。"""
        matcher = LayoutMatcher()
        slide_spec = SlideSpec(
            title="测试",
            items=[
                SlideItem(type=SlideItemType.PARAGRAPH, content="内容"),
            ],
            layout_hint="Title and Content",
        )

        selected = matcher.select_layout(slide_spec, sample_layouts)

        assert selected is not Nothing
        assert selected.unwrap().name == "Title and Content"

    def test_select_layout_with_blank_layout(self, sample_layouts: list) -> None:
        """测试选择Blank布局。"""
        matcher = LayoutMatcher()
        slide_spec = SlideSpec(title="测试", items=[], layout_hint="Blank")

        selected = matcher.select_layout(slide_spec, sample_layouts)

        assert selected is not Nothing
        assert selected.unwrap().name == "Blank"
