"""预渲染管线模块。

提供代码高亮、Mermaid图表、LaTeX公式等复杂内容的预渲染功能。
所有预渲染器都实现统一的接口，支持通过配置启用或禁用。

预渲染流程:
    1. 检测需要预渲染的内容项
    2. 根据内容类型选择对应的预渲染器
    3. 执行预渲染，生成图片或HTML
    4. 将预渲染结果缓存到SlideItem的meta中
    5. 渲染阶段使用预渲染结果

预渲染器:
    - CodeHighlighter: 代码块语法高亮，生成带样式的图片
    - MermaidRenderer: Mermaid图表渲染，生成SVG或PNG图片
    - LatexRenderer: LaTeX公式渲染，生成图片

配置项:
    - enable_code: 是否启用代码高亮
    - enable_mermaid: 是否启用Mermaid渲染
    - enable_latex: 是否启用LaTeX渲染
    - cache_dir: 缓存目录路径
    - dpi: 输出图片分辨率
"""

from ..core.models import PrerenderConfig
from .base import BasePrerenderer
from .code_highlight import CodeHighlighter
from .latex_renderer import LatexRenderer
from .mermaid_renderer import MermaidRenderer
from .pipeline import (
    prerender_slide_items,
    prerender_slides,
)

__all__ = [
    "prerender_slides",
    "prerender_slide_items",
    "PrerenderConfig",
    "BasePrerenderer",
    "CodeHighlighter",
    "MermaidRenderer",
    "LatexRenderer",
]
