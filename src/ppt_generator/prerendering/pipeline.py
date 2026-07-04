"""预渲染管线组合器。

将所有预渲染器组合成一个统一的预渲染管线，处理幻灯片中的所有需要预渲染的内容。

预渲染流程:
    1. 遍历所有幻灯片
    2. 检测每个幻灯片中的内容项是否需要预渲染
    3. 根据内容类型选择对应的预渲染器
    4. 执行预渲染，生成图片
    5. 将预渲染结果缓存到SlideItem的meta中
    6. 返回更新后的幻灯片列表

支持的预渲染类型:
    - CODE: 代码块语法高亮
    - MERMAID: Mermaid图表
    - LATEX: LaTeX公式

设计原则:
    1. 纯函数式：不修改输入数据，返回新的SlideSpec列表
    2. 可配置：支持通过PrerenderConfig启用/禁用特定预渲染器
    3. 缓存优先：相同内容只渲染一次，结果缓存到磁盘
    4. 优雅降级：如果预渲染失败，保持原始内容不变
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from ..core.models import (
    PrerenderConfig,
    PrerenderResult,
    SlideItem,
    SlideItemType,
    SlideSpec,
    StyleConfig,
)
from .code_highlight import CodeHighlighter
from .latex_renderer import LatexRenderer
from .mermaid_renderer import MermaidRenderer

logger = logging.getLogger(__name__)

# 预渲染器函数类型：接受内容和可选额外参数，返回 PrerenderResult 或 None
RendererFn = Callable[..., PrerenderResult | None]


def prerender_slides(
    slides: list[SlideSpec],
    style_config: StyleConfig,
    prerender_config: PrerenderConfig | None = None,
) -> list[SlideSpec]:
    """对幻灯片列表执行预渲染。

    参数:
        slides: 幻灯片规格列表。
        style_config: 样式配置。
        prerender_config: 预渲染配置，可选。

    返回:
        更新后的幻灯片规格列表，包含预渲染结果。
    """
    config = prerender_config or PrerenderConfig()
    return [prerender_slide(slide, style_config, config) for slide in slides]


def prerender_slide(
    slide: SlideSpec,
    style_config: StyleConfig,
    prerender_config: PrerenderConfig,
) -> SlideSpec:
    """对单个幻灯片执行预渲染。

    参数:
        slide: 幻灯片规格。
        style_config: 样式配置。
        prerender_config: 预渲染配置。

    返回:
        更新后的幻灯片规格，包含预渲染结果。
    """
    new_items = prerender_slide_items(slide.items, style_config, prerender_config)
    return SlideSpec(
        title=slide.title,
        items=new_items,
        layout_hint=slide.layout_hint,
    )


def prerender_slide_items(
    items: list[SlideItem],
    style_config: StyleConfig,
    prerender_config: PrerenderConfig,
) -> list[SlideItem]:
    """对幻灯片内容项列表执行预渲染。

    参数:
        items: 内容项列表。
        style_config: 样式配置。
        prerender_config: 预渲染配置。

    返回:
        更新后的内容项列表，包含预渲染结果。
    """
    renderers = _create_renderers(style_config, prerender_config)
    return [_prerender_item(item, renderers) for item in items]


def _create_renderers(
    style_config: StyleConfig,
    prerender_config: PrerenderConfig,
) -> dict[str, RendererFn]:
    """声明式创建预渲染器映射。"""
    candidates: list[tuple[str, bool, type, Any]] = [
        ("code", prerender_config.enable_code, CodeHighlighter, style_config.code),
        ("mermaid", prerender_config.enable_mermaid, MermaidRenderer, style_config.mermaid),
        ("latex", prerender_config.enable_latex, LatexRenderer, style_config.latex),
    ]
    return {
        name: cls(prerender_config, style).prerender
        for name, enabled, cls, style in candidates
        if enabled
    }


def _prerender_item(
    item: SlideItem,
    renderers: dict[str, RendererFn],
) -> SlideItem:
    """对单个内容项执行预渲染。

    参数:
        item: 内容项。
        renderers: 预渲染器映射。

    返回:
        更新后的内容项，如果预渲染成功则包含预渲染结果。
    """
    if item.type == SlideItemType.CODE:
        language = item.meta.get("language", "").lower()

        if language == "mermaid" and "mermaid" in renderers:
            return _try_prerender(
                item,
                renderers["mermaid"],
                item.content,
                label="Mermaid图表",
            )

        if "code" in renderers:
            return _try_prerender(
                item,
                renderers["code"],
                item.content,
                item.meta.get("language", ""),
                label=f"代码块（语言: {item.meta.get('language', '')}）",
            )

    if item.type == SlideItemType.PARAGRAPH:
        return _prerender_paragraph(item, renderers)

    return item


def _try_prerender(
    item: SlideItem,
    renderer: RendererFn,
    *args: str,
    label: str = "内容",
) -> SlideItem:
    """尝试预渲染，成功则返回带预渲染结果的 SlideItem，失败则返回原 item。

    高阶组合器，统一处理"渲染→包装→日志"模式。

    参数:
        item: 原始内容项。
        renderer: 预渲染器函数。
        *args: 传递给渲染器的额外参数。
        label: 日志标签。

    返回:
        更新后的内容项（如果成功）或原始内容项（如果失败）。
    """
    result = renderer(*args)

    if result:
        new_meta = {**item.meta, "prerender": result}
        logger.debug(f"{label}预渲染成功")
        return SlideItem(type=item.type, content=item.content, meta=new_meta)

    logger.debug(f"{label}预渲染失败")
    return item


def _prerender_paragraph(
    item: SlideItem,
    renderers: dict[str, RendererFn],
) -> SlideItem:
    """预渲染段落中的Mermaid和LaTeX内容。

    使用 try_prerender 高阶函数链式尝试，第一个成功的结果即返回。

    参数:
        item: 段落内容项。
        renderers: 预渲染器映射。

    返回:
        更新后的内容项，如果预渲染成功则包含预渲染结果。
    """
    content = item.content

    # 定义检测-渲染策略列表，按优先级排序
    strategies: list[tuple[str, RendererFn | None, Callable[[str], str | None]]] = [
        ("Mermaid图表", renderers.get("mermaid"), _detect_mermaid_content),
        ("LaTeX公式", renderers.get("latex"), _detect_latex_content),
    ]

    for label, renderer, detector in strategies:
        if renderer is None:
            continue

        detected_content = detector(content)
        if detected_content is not None:
            result = renderer(detected_content)
            if result:
                new_meta = {**item.meta, "prerender": result}
                logger.debug(f"{label}预渲染成功")
                return SlideItem(type=SlideItemType.IMAGE, content=content, meta=new_meta)
            logger.debug(f"{label}预渲染失败")

    return item


def _detect_mermaid_content(content: str) -> str | None:
    """检测内容是否为Mermaid图表，返回图表代码或None。"""
    mermaid_patterns = [
        "graph",
        "flowchart",
        "sequenceDiagram",
        "classDiagram",
        "stateDiagram",
        "gantt",
        "pie",
        "erDiagram",
        "journey",
    ]

    lines = content.strip().split("\n")
    if lines and any(lines[0].strip().startswith(pattern) for pattern in mermaid_patterns):
        return content

    return None


def _detect_latex_content(content: str) -> str | None:
    """检测内容是否为LaTeX公式，返回公式代码或None。"""
    content = content.strip()

    if content.startswith("$$") and content.endswith("$$") and len(content) > 4:
        return content[2:-2]

    if content.startswith("$") and content.endswith("$") and len(content) > 2:
        return content[1:-1]

    if content.startswith(r"\[") and content.endswith(r"\]") and len(content) > 4:
        return content[2:-2]

    return None


def clear_cache(config: PrerenderConfig) -> None:
    """清除预渲染缓存。

    参数:
        config: 预渲染配置。
    """
    cache_dir = config.cache_dir
    if cache_dir.exists():
        import shutil

        shutil.rmtree(cache_dir)
        logger.info(f"预渲染缓存已清除: {cache_dir}")


def get_cache_stats(config: PrerenderConfig) -> dict[str, int]:
    """获取缓存统计信息。

    参数:
        config: 预渲染配置。

    返回:
        缓存统计字典，包含各类型缓存文件数量。
    """
    return {
        name: len(list((config.cache_dir / name).glob("*.png")))
        if (config.cache_dir / name).exists()
        else 0
        for name in ("code", "mermaid", "latex")
    }
