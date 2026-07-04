"""渲染模块。

提供PPT渲染相关的IO操作和内容渲染功能。
"""

from .io_effects import (
    load_presentation,
    save_presentation,
    find_layout_index,
    add_slide,
    render_title,
    get_body_text_frame,
    set_autofit,
    apply_run_style,
    render_rich_paragraph,
    render_paragraph,
    render_list,
    render_rich_list,
    extract_layouts,
    render_slide_item,
    render_default_item,
    render_image,
)


__all__ = [
    "load_presentation",
    "save_presentation",
    "find_layout_index",
    "add_slide",
    "render_title",
    "get_body_text_frame",
    "set_autofit",
    "apply_run_style",
    "render_rich_paragraph",
    "render_paragraph",
    "render_list",
    "render_rich_list",
    "extract_layouts",
    "render_slide_item",
    "render_default_item",
    "render_image",
]
