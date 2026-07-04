"""自动分页模块单元测试。

覆盖 PaginationConfig 验证、高度估算函数、分页算法等。
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from ppt_generator.core.models import (
    LayoutSpec,
    PlaceholderSpec,
    PrerenderResult,
    SlideItem,
    SlideItemType,
    SlideSpec,
    StyleConfig,
)
from ppt_generator.matching.pagination import (
    PaginationConfig,
    _emu_to_pt,
    _estimate_code_height,
    _estimate_image_height,
    _estimate_item_height,
    _estimate_list_height,
    _estimate_paragraph_height,
    _estimate_table_height,
    _get_body_dimensions,
    _get_body_height_from_layout,
    _pt_to_emu,
    _px_to_emu,
    paginate_slide,
    paginate_slides,
)

# ──────────────────────── 工具函数测试 ────────────────────────


class TestUnitConversion:
    """测试 EMU/磅/像素 互转函数。"""

    def test_emu_to_pt_default_dpi(self) -> None:
        """1 英寸 = 914400 EMU = 72 磅。"""
        assert _emu_to_pt(914400) == pytest.approx(72.0)

    def test_emu_to_pt_zero(self) -> None:
        assert _emu_to_pt(0) == 0.0

    def test_pt_to_emu_round_trip(self) -> None:
        """磅→EMU 应与 EMU→磅 大致可逆。"""
        pt = 18.0
        emu = _pt_to_emu(pt)
        assert _emu_to_pt(emu) == pytest.approx(pt, abs=1)

    def test_pt_to_emu_known_value(self) -> None:
        """72 磅 = 914400 EMU。"""
        assert _pt_to_emu(72) == 914400

    def test_px_to_emu_default_dpi(self) -> None:
        """96 dpi 下 96 像素 = 914400 EMU。"""
        assert _px_to_emu(96, dpi=96) == 914400

    def test_px_to_emu_custom_dpi(self) -> None:
        assert _px_to_emu(300, dpi=300) == 914400


# ──────────────────────── PaginationConfig 测试 ────────────────────────


class TestPaginationConfig:
    """测试 PaginationConfig 的字段验证与回退。"""

    def test_default_values(self) -> None:
        config = PaginationConfig()
        assert config.enable is True
        assert config.min_items_per_page == 1
        assert config.max_items_per_page == 0
        assert config.title_suffix == "（续）"
        assert config.base_font_size == 18
        assert config.line_height_ratio == 1.5
        assert config.dpi == 96

    def test_invalid_min_items_clamped_to_1(self) -> None:
        """min_items_per_page 小于 1 时回退为 1。"""
        config = PaginationConfig(min_items_per_page=-3)
        assert config.min_items_per_page == 1

    def test_invalid_max_items_clamped_to_0(self) -> None:
        """max_items_per_page 小于 0 时回退为 0（不限制）。"""
        config = PaginationConfig(max_items_per_page=-5)
        assert config.max_items_per_page == 0

    def test_invalid_font_size_reset_to_default(self) -> None:
        config = PaginationConfig(base_font_size=0)
        assert config.base_font_size == 18

    def test_invalid_line_height_reset_to_default(self) -> None:
        config = PaginationConfig(line_height_ratio=-1.0)
        assert config.line_height_ratio == 1.5

    def test_invalid_dpi_reset_to_default(self) -> None:
        config = PaginationConfig(dpi=0)
        assert config.dpi == 96

    def test_frozen_dataclass_cannot_assign(self) -> None:
        """PaginationConfig 是 frozen dataclass，赋值应抛 FrozenInstanceError。"""
        config = PaginationConfig()
        with pytest.raises(dataclasses.FrozenInstanceError):
            config.enable = False


# ──────────────────────── 高度估算函数测试 ────────────────────────


class TestEstimateParagraphHeight:
    """测试段落高度估算。"""

    def test_empty_content_returns_zero(self) -> None:
        item = SlideItem(type=SlideItemType.PARAGRAPH, content="")
        config = PaginationConfig()
        assert _estimate_paragraph_height(item, config, 9144000) == 0

    def test_short_text_returns_positive_height(self) -> None:
        item = SlideItem(type=SlideItemType.PARAGRAPH, content="短文本")
        config = PaginationConfig()
        height = _estimate_paragraph_height(item, config, 9144000)
        assert height > 0

    def test_long_text_taller_than_short_text(self) -> None:
        """长文本应比短文本占用更多高度。"""
        config = PaginationConfig()
        short_item = SlideItem(type=SlideItemType.PARAGRAPH, content="短")
        long_item = SlideItem(
            type=SlideItemType.PARAGRAPH,
            content="这是一段非常非常非常非常非常非常非常非常非常非常长的文本" * 10,
        )
        short_h = _estimate_paragraph_height(short_item, config, 9144000)
        long_h = _estimate_paragraph_height(long_item, config, 9144000)
        assert long_h > short_h

    def test_zero_container_width_uses_default_chars(self) -> None:
        """容器宽度为 0 时应使用默认每行字符数 30。"""
        item = SlideItem(type=SlideItemType.PARAGRAPH, content="x" * 60)
        config = PaginationConfig()
        # 不应抛异常，且应返回正高度
        height = _estimate_paragraph_height(item, config, 0)
        assert height > 0


class TestEstimateListHeight:
    """测试列表项高度估算。"""

    def test_empty_content_returns_zero(self) -> None:
        item = SlideItem(type=SlideItemType.LIST, content="")
        config = PaginationConfig()
        assert _estimate_list_height(item, config, 9144000) == 0

    def test_list_returns_positive_height(self) -> None:
        item = SlideItem(type=SlideItemType.LIST, content="列表项")
        config = PaginationConfig()
        assert _estimate_list_height(item, config, 9144000) > 0

    def test_zero_container_width_uses_default_chars(self) -> None:
        item = SlideItem(type=SlideItemType.LIST, content="x" * 50)
        config = PaginationConfig()
        height = _estimate_list_height(item, config, 0)
        assert height > 0


class TestEstimateCodeHeight:
    """测试代码块高度估算。"""

    def test_empty_content_returns_zero(self) -> None:
        item = SlideItem(type=SlideItemType.CODE, content="")
        config = PaginationConfig()
        style = StyleConfig()
        assert _estimate_code_height(item, config, style) == 0

    def test_text_only_code_returns_positive_height(self) -> None:
        item = SlideItem(type=SlideItemType.CODE, content="print('hello')")
        config = PaginationConfig()
        style = StyleConfig()
        assert _estimate_code_height(item, config, style) > 0

    def test_multiline_code_taller_than_single_line(self) -> None:
        config = PaginationConfig()
        style = StyleConfig()
        single = SlideItem(type=SlideItemType.CODE, content="print(1)")
        multi = SlideItem(
            type=SlideItemType.CODE,
            content="print(1)\nprint(2)\nprint(3)\nprint(4)\nprint(5)",
        )
        assert _estimate_code_height(multi, config, style) > _estimate_code_height(
            single, config, style
        )

    def test_prerender_result_uses_image_height(self) -> None:
        """有预渲染结果时使用图片实际高度。"""
        prerender = PrerenderResult(
            image_path=Path("/tmp/fake.png"), width=400, height=300, content_hash="abc"
        )
        item = SlideItem(
            type=SlideItemType.CODE,
            content="print('hi')",
            meta={"prerender": prerender},
        )
        config = PaginationConfig(dpi=96)
        style = StyleConfig()
        height = _estimate_code_height(item, config, style)
        # 300 像素 @ 96 dpi = 300 * 914400 / 96 EMU
        expected = int(300 * 914400 / 96)
        assert height == expected


class TestEstimateImageHeight:
    """测试图片高度估算。"""

    def test_with_prerender_no_scaling(self) -> None:
        """有预渲染结果且图片宽度小于容器时直接使用图片高度。"""
        prerender = PrerenderResult(
            image_path=Path("/tmp/fake.png"), width=200, height=100, content_hash="abc"
        )
        item = SlideItem(
            type=SlideItemType.IMAGE, content="", meta={"prerender": prerender}
        )
        config = PaginationConfig(dpi=96)
        # 容器宽度大于图片宽度（200px @ 96dpi = 1905000 EMU），不应缩放
        height = _estimate_image_height(item, config, 9144000)
        expected = int(100 * 914400 / 96)
        assert height == expected

    def test_with_prerender_scaled_down(self) -> None:
        """图片宽度大于容器时按比例缩放。"""
        prerender = PrerenderResult(
            image_path=Path("/tmp/fake.png"), width=400, height=200, content_hash="abc"
        )
        item = SlideItem(
            type=SlideItemType.IMAGE, content="", meta={"prerender": prerender}
        )
        config = PaginationConfig(dpi=96)
        # 图片 400px = 3810000 EMU，容器 1905000 EMU，比例 0.5
        height = _estimate_image_height(item, config, 1905000)
        expected = int(int(200 * 914400 / 96) * 0.5)
        assert height == expected

    def test_without_prerender_uses_container_width(self) -> None:
        """无预渲染结果时按容器宽度的 60% 估算高度。"""
        item = SlideItem(type=SlideItemType.IMAGE, content="")
        config = PaginationConfig()
        height = _estimate_image_height(item, config, 1000000)
        assert height == 600000

    def test_without_prerender_zero_container(self) -> None:
        """无预渲染结果且容器为 0 时返回固定 200 磅的 EMU。"""
        item = SlideItem(type=SlideItemType.IMAGE, content="")
        config = PaginationConfig(dpi=96)
        height = _estimate_image_height(item, config, 0)
        assert height == _pt_to_emu(200, 96)


class TestEstimateTableHeight:
    """测试表格高度估算。"""

    def test_with_rows_meta(self) -> None:
        item = SlideItem(
            type=SlideItemType.TABLE, content="", meta={"rows": 5}
        )
        config = PaginationConfig()
        style = StyleConfig()
        height = _estimate_table_height(item, config, style)
        font_size = style.table.font_size
        expected = _pt_to_emu(5 * font_size * 1.8, config.dpi)
        assert height == expected

    def test_without_rows_meta_uses_content_lines(self) -> None:
        """无 rows 元数据时按内容换行数估算。"""
        item = SlideItem(
            type=SlideItemType.TABLE, content="行1\n行2\n行3", meta={}
        )
        config = PaginationConfig()
        style = StyleConfig()
        height = _estimate_table_height(item, config, style)
        font_size = style.table.font_size
        expected = _pt_to_emu(3 * font_size * 1.8, config.dpi)
        assert height == expected


class TestEstimateItemHeight:
    """测试 _estimate_item_height 分发逻辑。"""

    def test_paragraph_dispatches_correctly(self) -> None:
        item = SlideItem(type=SlideItemType.PARAGRAPH, content="段落")
        config = PaginationConfig()
        style = StyleConfig()
        height = _estimate_item_height(item, config, style, 9144000)
        assert height == _estimate_paragraph_height(item, config, 9144000)

    def test_list_dispatches_correctly(self) -> None:
        item = SlideItem(type=SlideItemType.LIST, content="列表项")
        config = PaginationConfig()
        style = StyleConfig()
        height = _estimate_item_height(item, config, style, 9144000)
        assert height == _estimate_list_height(item, config, 9144000)

    def test_code_dispatches_correctly(self) -> None:
        item = SlideItem(type=SlideItemType.CODE, content="x = 1")
        config = PaginationConfig()
        style = StyleConfig()
        height = _estimate_item_height(item, config, style, 9144000)
        assert height == _estimate_code_height(item, config, style)

    def test_image_dispatches_correctly(self) -> None:
        item = SlideItem(type=SlideItemType.IMAGE, content="")
        config = PaginationConfig()
        style = StyleConfig()
        height = _estimate_item_height(item, config, style, 9144000)
        assert height == _estimate_image_height(item, config, 9144000)

    def test_table_dispatches_correctly(self) -> None:
        item = SlideItem(type=SlideItemType.TABLE, content="", meta={"rows": 2})
        config = PaginationConfig()
        style = StyleConfig()
        height = _estimate_item_height(item, config, style, 9144000)
        assert height == _estimate_table_height(item, config, style)

    def test_heading_falls_back_to_paragraph(self) -> None:
        """未知类型（如 HEADING）回退到段落估算。"""
        item = SlideItem(type=SlideItemType.HEADING, content="标题")
        config = PaginationConfig()
        style = StyleConfig()
        height = _estimate_item_height(item, config, style, 9144000)
        assert height == _estimate_paragraph_height(item, config, 9144000)


# ──────────────────────── 布局辅助函数测试 ────────────────────────


def _make_layout(name: str, ph_type: str | None = None) -> LayoutSpec:
    """构造测试用 LayoutSpec。"""
    placeholders = []
    if ph_type:
        placeholders.append(
            PlaceholderSpec(
                name=f"{ph_type} 1", placeholder_type=ph_type, index=0, shape_id=1
            )
        )
    return LayoutSpec(name=name, placeholders=placeholders)


class TestGetBodyDimensions:
    """测试 _get_body_dimensions。"""

    def test_finds_body_placeholder(self) -> None:
        layout = _make_layout("Title and Content", ph_type="BODY")
        width, height = _get_body_dimensions(layout)
        # 当前实现命中匹配时返回默认尺寸
        assert width == 8000000
        assert height == 4000000

    def test_finds_object_placeholder(self) -> None:
        layout = _make_layout("Content", ph_type="OBJECT")
        width, height = _get_body_dimensions(layout)
        assert width == 8000000
        assert height == 4000000

    def test_finds_subtitle_placeholder(self) -> None:
        layout = _make_layout("Title Slide", ph_type="SUBTITLE")
        width, height = _get_body_dimensions(layout)
        assert width == 8000000
        assert height == 4000000

    def test_finds_content_placeholder(self) -> None:
        layout = _make_layout("Blank", ph_type="CONTENT")
        width, height = _get_body_dimensions(layout)
        assert width == 8000000
        assert height == 4000000

    def test_no_matching_placeholder_returns_default(self) -> None:
        """无匹配占位符时返回默认尺寸。"""
        layout = _make_layout("Blank", ph_type="title")
        width, height = _get_body_dimensions(layout)
        assert width == 8000000
        assert height == 4000000


class TestGetBodyHeightFromLayout:
    """测试 _get_body_height_from_layout 的启发式估算。"""

    @pytest.mark.parametrize(
        ("name", "expected"),
        [
            ("Title Slide", 2000000),
            ("Title-Slide", 2000000),
            ("Section Header", 1500000),
            ("Section-Header", 1500000),
            ("Two Content", 3500000),
            ("Two-Content", 3500000),
            ("Picture with Caption", 4000000),
            ("Blank", 5000000),
            ("Title and Content", 4000000),  # 默认
            ("Unknown Layout", 4000000),  # 默认
        ],
    )
    def test_layout_height_estimation(self, name: str, expected: int) -> None:
        layout = _make_layout(name)
        assert _get_body_height_from_layout(layout) == expected


# ──────────────────────── paginate_slide 测试 ────────────────────────


class TestPaginateSlide:
    """测试 paginate_slide 主分页函数。"""

    def test_disabled_pagination_returns_original(self) -> None:
        """config.enable=False 时返回原始幻灯片。"""
        config = PaginationConfig(enable=False)
        item = SlideItem(type=SlideItemType.PARAGRAPH, content="内容" * 100)
        slide = SlideSpec(title="测试", items=[item])
        layout = _make_layout("Title and Content")
        style = StyleConfig()

        result = paginate_slide(slide, layout, style, config)
        assert len(result) == 1
        assert result[0] is slide

    def test_few_items_no_pagination(self) -> None:
        """内容项少于阈值且无 max 限制时返回单页。"""
        config = PaginationConfig()
        slide = SlideSpec(
            title="测试",
            items=[SlideItem(type=SlideItemType.PARAGRAPH, content="短内容")],
        )
        layout = _make_layout("Title and Content")
        style = StyleConfig()

        result = paginate_slide(slide, layout, style, config)
        assert len(result) == 1
        assert result[0] is slide

    def test_max_items_per_page_forces_pagination(self) -> None:
        """max_items_per_page 强制分页。"""
        config = PaginationConfig(max_items_per_page=2)
        items = [
            SlideItem(type=SlideItemType.LIST, content=f"项 {i}") for i in range(5)
        ]
        slide = SlideSpec(title="列表页", items=items)
        layout = _make_layout("Title and Content")
        style = StyleConfig()

        result = paginate_slide(slide, layout, style, config)
        assert len(result) == 3  # 5 项 / 每页 2 项 = 3 页
        # 第一页 2 项
        assert len(result[0].items) == 2
        # 第二页 2 项
        assert len(result[1].items) == 2
        # 第三页 1 项
        assert len(result[2].items) == 1

    def test_continuation_pages_get_suffix(self) -> None:
        """续页标题加上 title_suffix。"""
        config = PaginationConfig(max_items_per_page=1, title_suffix="（续）")
        items = [
            SlideItem(type=SlideItemType.LIST, content=f"项 {i}") for i in range(3)
        ]
        slide = SlideSpec(title="议程", items=items)
        layout = _make_layout("Title and Content")
        style = StyleConfig()

        result = paginate_slide(slide, layout, style, config)
        assert len(result) == 3
        assert result[0].title == "议程"
        assert result[1].title == "议程（续）"
        assert result[2].title == "议程（续）"

    def test_empty_title_continuation_no_suffix(self) -> None:
        """空标题时续页不加后缀。"""
        config = PaginationConfig(max_items_per_page=1, title_suffix="（续）")
        items = [
            SlideItem(type=SlideItemType.LIST, content=f"项 {i}") for i in range(2)
        ]
        slide = SlideSpec(title="", items=items)
        layout = _make_layout("Title and Content")
        style = StyleConfig()

        result = paginate_slide(slide, layout, style, config)
        assert len(result) == 2
        assert result[0].title == ""
        assert result[1].title == ""

    def test_layout_hint_preserved(self) -> None:
        """分页后 layout_hint 应保留。"""
        config = PaginationConfig(max_items_per_page=1)
        items = [
            SlideItem(type=SlideItemType.LIST, content=f"项 {i}") for i in range(2)
        ]
        slide = SlideSpec(title="议程", items=items, layout_hint="Title and Content")
        layout = _make_layout("Title and Content")
        style = StyleConfig()

        result = paginate_slide(slide, layout, style, config)
        for page in result:
            assert page.layout_hint == "Title and Content"

    def test_content_overflow_triggers_pagination(self) -> None:
        """内容过多（超过容器高度）时触发分页。"""
        config = PaginationConfig()
        # 构造大量长文本段落，确保总高度超过 available_h（4000000 EMU）
        long_text = "x" * 500
        items = [
            SlideItem(type=SlideItemType.PARAGRAPH, content=long_text) for _ in range(20)
        ]
        slide = SlideSpec(title="长内容", items=items)
        layout = _make_layout("Title and Content")
        style = StyleConfig()

        result = paginate_slide(slide, layout, style, config)
        assert len(result) > 1

    def test_no_pagination_when_only_one_page_needed(self) -> None:
        """内容刚好一页时返回原始幻灯片。"""
        config = PaginationConfig()
        items = [
            SlideItem(type=SlideItemType.PARAGRAPH, content="短内容"),
        ]
        slide = SlideSpec(title="单页", items=items)
        layout = _make_layout("Title and Content")
        style = StyleConfig()

        result = paginate_slide(slide, layout, style, config)
        assert len(result) == 1
        assert result[0] is slide


# ──────────────────────── paginate_slides 测试 ────────────────────────


class TestPaginateSlides:
    """测试 paginate_slides 批量分页函数。"""

    def test_disabled_returns_input_unchanged(self) -> None:
        """config.enable=False 时返回输入列表。"""
        config = PaginationConfig(enable=False)
        slide = SlideSpec(title="测试", items=[SlideItem(type=SlideItemType.PARAGRAPH, content="x")])
        layout = _make_layout("Title and Content")
        style = StyleConfig()

        result = paginate_slides([(slide, layout)], style, config)
        assert result == [(slide, layout)]

    def test_multiple_slides_each_paginated(self) -> None:
        """多张幻灯片各自独立分页。"""
        config = PaginationConfig(max_items_per_page=1)
        slide1 = SlideSpec(
            title="页1",
            items=[SlideItem(type=SlideItemType.LIST, content="a"),
                   SlideItem(type=SlideItemType.LIST, content="b")],
        )
        slide2 = SlideSpec(
            title="页2",
            items=[SlideItem(type=SlideItemType.LIST, content="c")],
        )
        layout = _make_layout("Title and Content")
        style = StyleConfig()

        result = paginate_slides([(slide1, layout), (slide2, layout)], style, config)
        # slide1 分 2 页，slide2 分 1 页，共 3 页
        assert len(result) == 3
        assert result[0][0].title == "页1"
        assert result[1][0].title == "页1（续）"
        assert result[2][0].title == "页2"

    def test_layout_preserved_in_result(self) -> None:
        """分页后每页都保留对应的 LayoutSpec。"""
        config = PaginationConfig(max_items_per_page=1)
        slide = SlideSpec(
            title="测试",
            items=[SlideItem(type=SlideItemType.LIST, content="a"),
                   SlideItem(type=SlideItemType.LIST, content="b")],
        )
        layout = _make_layout("Title and Content")
        style = StyleConfig()

        result = paginate_slides([(slide, layout)], style, config)
        for _, retained_layout in result:
            assert retained_layout is layout

    def test_empty_input_returns_empty(self) -> None:
        config = PaginationConfig()
        style = StyleConfig()
        assert paginate_slides([], style, config) == []
