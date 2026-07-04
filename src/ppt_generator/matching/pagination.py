"""自动分页模块。

当单页幻灯片内容过多时，自动将内容分配到多页，
保持内容项完整性，避免内容溢出占位符。

设计原则:
1. 纯函数式：不修改输入，返回新的幻灯片列表
2. 内容完整性：不在内容项中间拆分
3. 自适应：基于布局占位符的可用高度动态计算
4. 可配置：支持自定义分页参数
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from ..core.models import (
    LayoutSpec,
    PrerenderResult,
    SlideItem,
    SlideItemType,
    SlideSpec,
    StyleConfig,
)
from ..utils import is_windows

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PaginationConfig:
    """分页配置。

    属性:
        enable: 是否启用自动分页。
        min_items_per_page: 每页最少内容项数量。
        max_items_per_page: 每页最多内容项数量（0表示不限制，由高度决定）。
        title_suffix: 续页标题后缀。
        base_font_size: 基础字体大小（磅）。
        line_height_ratio: 行高系数。
        paragraph_spacing: 段落间距（磅）。
        list_item_spacing: 列表项间距（磅）。
        dpi: DPI用于像素到磅的转换。
    """

    enable: bool = True
    min_items_per_page: int = 1
    max_items_per_page: int = 0
    title_suffix: str = "（续）"
    base_font_size: int = 18
    line_height_ratio: float = 1.5
    paragraph_spacing: int = 6
    list_item_spacing: int = 4
    dpi: int = 96

    def __post_init__(self) -> None:
        """验证分页配置。"""
        if self.min_items_per_page < 1:
            object.__setattr__(self, "min_items_per_page", 1)
        if self.max_items_per_page < 0:
            object.__setattr__(self, "max_items_per_page", 0)
        if self.base_font_size <= 0:
            object.__setattr__(self, "base_font_size", 18)
        if self.line_height_ratio <= 0:
            object.__setattr__(self, "line_height_ratio", 1.5)
        if self.dpi <= 0:
            object.__setattr__(self, "dpi", 96)


def _estimate_paragraph_height(
    item: SlideItem,
    config: PaginationConfig,
    container_width_emu: int,
) -> int:
    """估算段落内容的高度（EMU）。

    参数:
        item: 段落内容项。
        config: 分页配置。
        container_width_emu: 容器宽度（EMU）。

    返回:
        估算的高度（EMU）。
    """
    text = item.content or ""
    if not text:
        return 0

    font_size_pt = config.base_font_size
    line_height_pt = font_size_pt * config.line_height_ratio
    spacing_pt = config.paragraph_spacing

    avg_char_width_pt = font_size_pt * 0.55
    container_width_pt = _emu_to_pt(container_width_emu, config.dpi)

    if container_width_pt <= 0:
        char_per_line = 30
    else:
        char_per_line = max(1, int(container_width_pt / avg_char_width_pt))

    text_length = len(text)
    num_lines = max(1, (text_length + char_per_line - 1) // char_per_line)

    total_height_pt = num_lines * line_height_pt + spacing_pt
    return _pt_to_emu(total_height_pt, config.dpi)


def _estimate_list_height(
    item: SlideItem,
    config: PaginationConfig,
    container_width_emu: int,
) -> int:
    """估算列表项的高度（EMU）。

    参数:
        item: 列表内容项。
        config: 分页配置。
        container_width_emu: 容器宽度（EMU）。

    返回:
        估算的高度（EMU）。
    """
    text = item.content or ""
    if not text:
        return 0

    font_size_pt = config.base_font_size
    line_height_pt = font_size_pt * config.line_height_ratio
    spacing_pt = config.list_item_spacing

    avg_char_width_pt = font_size_pt * 0.5
    indent_pt = font_size_pt * 1.5
    container_width_pt = _emu_to_pt(container_width_emu, config.dpi) - indent_pt

    if container_width_pt <= 0:
        char_per_line = 25
    else:
        char_per_line = max(1, int(container_width_pt / avg_char_width_pt))

    text_length = len(text)
    num_lines = max(1, (text_length + char_per_line - 1) // char_per_line)

    total_height_pt = num_lines * line_height_pt + spacing_pt
    return _pt_to_emu(total_height_pt, config.dpi)


def _estimate_code_height(
    item: SlideItem,
    config: PaginationConfig,
    style_config: StyleConfig,
) -> int:
    """估算代码块的高度（EMU）。

    如果代码已预渲染为图片，使用图片实际高度；
    否则根据代码行数估算。

    参数:
        item: 代码内容项。
        config: 分页配置。
        style_config: 样式配置。

    返回:
        估算的高度（EMU）。
    """
    prerender = item.meta.get("prerender")
    if isinstance(prerender, PrerenderResult) and prerender.height > 0:
        return _px_to_emu(prerender.height, config.dpi)

    text = item.content or ""
    if not text:
        return 0

    lines = text.count("\n") + 1
    font_size_pt = style_config.code.font_size
    line_height_pt = font_size_pt * style_config.code.line_height
    padding_pt = style_config.code.padding * 2

    total_height_pt = lines * line_height_pt + padding_pt
    return _pt_to_emu(total_height_pt, config.dpi)


def _estimate_image_height(
    item: SlideItem,
    config: PaginationConfig,
    container_width_emu: int,
) -> int:
    """估算图片的高度（EMU）。

    如果图片有预渲染结果，使用实际尺寸等比缩放；
    否则根据容器宽度估算。

    参数:
        item: 图片内容项。
        config: 分页配置。
        container_width_emu: 容器宽度（EMU）。

    返回:
        估算的高度（EMU）。
    """
    prerender = item.meta.get("prerender")
    if isinstance(prerender, PrerenderResult) and prerender.width > 0 and prerender.height > 0:
        img_w_emu = _px_to_emu(prerender.width, config.dpi)
        img_h_emu = _px_to_emu(prerender.height, config.dpi)

        if container_width_emu > 0 and img_w_emu > container_width_emu:
            ratio = container_width_emu / img_w_emu
            return int(img_h_emu * ratio)
        return img_h_emu

    if container_width_emu > 0:
        return int(container_width_emu * 0.6)

    return _pt_to_emu(200, config.dpi)


def _estimate_table_height(
    item: SlideItem,
    config: PaginationConfig,
    style_config: StyleConfig,
) -> int:
    """估算表格的高度（EMU）。

    参数:
        item: 表格内容项。
        config: 分页配置。
        style_config: 样式配置。

    返回:
        估算的高度（EMU）。
    """
    rows = item.meta.get("rows", 0)
    if rows <= 0:
        text = item.content or ""
        rows = max(1, text.count("\n") + 1)

    font_size_pt = style_config.table.font_size
    row_height_pt = font_size_pt * 1.8

    total_height_pt = rows * row_height_pt
    return _pt_to_emu(total_height_pt, config.dpi)


def _estimate_item_height(
    item: SlideItem,
    config: PaginationConfig,
    style_config: StyleConfig,
    container_width_emu: int,
) -> int:
    """估算单个内容项的高度（EMU）。

    参数:
        item: 内容项。
        config: 分页配置。
        style_config: 样式配置。
        container_width_emu: 容器宽度（EMU）。

    返回:
        估算的高度（EMU）。
    """
    if item.type == SlideItemType.PARAGRAPH:
        return _estimate_paragraph_height(item, config, container_width_emu)
    elif item.type == SlideItemType.LIST:
        return _estimate_list_height(item, config, container_width_emu)
    elif item.type == SlideItemType.CODE:
        return _estimate_code_height(item, config, style_config)
    elif item.type == SlideItemType.IMAGE:
        return _estimate_image_height(item, config, container_width_emu)
    elif item.type == SlideItemType.TABLE:
        return _estimate_table_height(item, config, style_config)
    else:
        return _estimate_paragraph_height(item, config, container_width_emu)


def _emu_to_pt(emu: int, dpi: int = 96) -> float:
    """EMU转磅。

    1英寸 = 914400 EMU = 72磅
    """
    return emu * 72 / 914400


def _pt_to_emu(pt: float, dpi: int = 96) -> int:
    """磅转EMU。"""
    return int(pt * 914400 / 72)


def _px_to_emu(px: int, dpi: int = 96) -> int:
    """像素转EMU。

    1英寸 = 914400 EMU = dpi像素
    """
    return int(px * 914400 / dpi)


def _get_body_dimensions(layout: LayoutSpec) -> tuple[int, int]:
    """从布局规格中获取BODY占位符的尺寸。

    优先查找BODY类型，其次是OBJECT、SUBTITLE。
    如果找不到，返回默认尺寸。

    参数:
        layout: 布局规格。

    返回:
        (宽度, 高度) EMU元组。
    """
    default_w = 8000000
    default_h = 4000000

    priority_types = ["BODY", "OBJECT", "SUBTITLE", "CONTENT"]

    for ph_type in priority_types:
        for ph in layout.placeholders:
            if ph.placeholder_type.upper() == ph_type:
                return default_w, default_h

    return default_w, default_h


def _get_body_height_from_layout(layout: LayoutSpec) -> int:
    """获取布局中正文区域的估算高度（EMU）。

    由于 LayoutSpec 中不存储占位符的物理尺寸，
    这里使用基于布局类型的启发式估算。

    参数:
        layout: 布局规格。

    返回:
        估算的正文区域高度（EMU）。
    """
    name_lower = layout.name.lower()

    if "title slide" in name_lower or "title-slide" in name_lower:
        return 2000000
    elif "section header" in name_lower or "section-header" in name_lower:
        return 1500000
    elif "two content" in name_lower or "two-content" in name_lower:
        return 3500000
    elif "picture" in name_lower:
        return 4000000
    elif "blank" in name_lower:
        return 5000000
    else:
        return 4000000


def paginate_slide(
    slide: SlideSpec,
    layout: LayoutSpec,
    style_config: StyleConfig,
    pagination_config: PaginationConfig | None = None,
) -> list[SlideSpec]:
    """将单个幻灯片按内容高度自动分页。

    使用首次适应（First-Fit）算法，
    将内容项分配到多页，保持内容项完整性。

    参数:
        slide: 原始幻灯片规格。
        layout: 匹配的布局规格。
        style_config: 样式配置。
        pagination_config: 分页配置，默认使用默认配置。

    返回:
        分页后的幻灯片规格列表。如果不需要分页，返回单元素列表。
    """
    config = pagination_config or PaginationConfig()

    if not config.enable:
        return [slide]

    items = slide.items
    if len(items) <= config.min_items_per_page and config.max_items_per_page == 0:
        return [slide]

    container_w, _ = _get_body_dimensions(layout)
    available_h = _get_body_height_from_layout(layout)

    if available_h <= 0:
        return [slide]

    pages: list[list[SlideItem]] = []
    current_page: list[SlideItem] = []
    current_height = 0

    for item in items:
        item_h = _estimate_item_height(item, config, style_config, container_w)

        fits_current = current_height + item_h <= available_h
        at_max = (
            config.max_items_per_page > 0
            and len(current_page) >= config.max_items_per_page
        )

        if current_page and (not fits_current or at_max):
            pages.append(current_page)
            current_page = []
            current_height = 0

        current_page.append(item)
        current_height += item_h

    if current_page:
        pages.append(current_page)

    if len(pages) <= 1:
        return [slide]

    result: list[SlideSpec] = []
    for idx, page_items in enumerate(pages):
        if idx == 0:
            title = slide.title
        else:
            title = slide.title + config.title_suffix if slide.title else slide.title

        result.append(
            SlideSpec(
                title=title,
                items=page_items,
                layout_hint=slide.layout_hint,
            )
        )

    logger.info(f"幻灯片 '{slide.title}' 自动分页为 {len(pages)} 页")
    return result


def paginate_slides(
    slides_with_layouts: list[tuple[SlideSpec, LayoutSpec]],
    style_config: StyleConfig,
    pagination_config: PaginationConfig | None = None,
) -> list[tuple[SlideSpec, LayoutSpec]]:
    """对所有幻灯片执行自动分页。

    参数:
        slides_with_layouts: (SlideSpec, LayoutSpec) 元组列表。
        style_config: 样式配置。
        pagination_config: 分页配置。

    返回:
        分页后的 (SlideSpec, LayoutSpec) 元组列表。
    """
    config = pagination_config or PaginationConfig()

    if not config.enable:
        return slides_with_layouts

    result: list[tuple[SlideSpec, LayoutSpec]] = []
    for slide, layout in slides_with_layouts:
        paginated = paginate_slide(slide, layout, style_config, config)
        for p_slide in paginated:
            result.append((p_slide, layout))

    return result
