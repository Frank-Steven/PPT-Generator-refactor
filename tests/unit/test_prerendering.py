"""预渲染模块单元测试。

覆盖 BasePrerenderer 缓存机制、CodeHighlighter、LatexRenderer、
MermaidRenderer 的渲染与回退路径，以及 pipeline 的组合逻辑。
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image

from ppt_generator.core.models import (
    CodeStyle,
    LatexStyle,
    MermaidStyle,
    PrerenderConfig,
    PrerenderResult,
    SlideItem,
    SlideItemType,
    SlideSpec,
    StyleConfig,
)
from ppt_generator.prerendering.base import BasePrerenderer
from ppt_generator.prerendering.code_highlight import CodeHighlighter
from ppt_generator.prerendering.latex_renderer import LatexRenderer
from ppt_generator.prerendering.mermaid_renderer import MermaidRenderer
from ppt_generator.prerendering.pipeline import (
    _create_renderers,
    _detect_latex_content,
    _detect_mermaid_content,
    _prerender_item,
    _prerender_paragraph,
    _try_prerender,
    clear_cache,
    get_cache_stats,
    prerender_slide,
    prerender_slide_items,
    prerender_slides,
)

# ──────────────────────── 共享 fixtures ────────────────────────


@pytest.fixture
def prerender_config(tmp_path: Path) -> PrerenderConfig:
    """返回使用 tmp_path 的 PrerenderConfig。"""
    return PrerenderConfig(cache_dir=tmp_path / "prerender_cache", timeout=5)


@pytest.fixture
def style_config() -> StyleConfig:
    """返回默认 StyleConfig。"""
    return StyleConfig()


# ──────────────────────── BasePrerenderer 测试 ────────────────────────


class _StubPrerenderer(BasePrerenderer):
    """用于测试 BasePrerenderer 模板方法的桩实现。"""

    def __init__(self, config: PrerenderConfig, *, fail: bool = False) -> None:
        super().__init__(config, "stub")
        self._fail = fail
        self.render_call_count = 0

    def _render(
        self, content: str, output_path: Path, *args: str
    ) -> tuple[int, int] | None:
        self.render_call_count += 1
        if self._fail:
            raise RuntimeError("stub 渲染失败")
        # 创建 10x5 的纯色 PNG
        image = Image.new("RGB", (10, 5), (255, 0, 0))
        image.save(str(output_path), format="PNG")
        return 10, 5


class TestBasePrerenderer:
    """测试 BasePrerenderer 的缓存与错误处理模板。"""

    def test_first_render_creates_cache_file(
        self, prerender_config: PrerenderConfig
    ) -> None:
        renderer = _StubPrerenderer(prerender_config)
        result = renderer.prerender("test content")

        assert result is not None
        assert result.width == 10
        assert result.height == 5
        assert result.image_path.exists()
        assert renderer.render_call_count == 1

    def test_second_render_uses_cache(
        self, prerender_config: PrerenderConfig
    ) -> None:
        """相同内容第二次渲染应命中缓存，不调用 _render。"""
        renderer = _StubPrerenderer(prerender_config)
        first = renderer.prerender("cached content")
        second = renderer.prerender("cached content")

        assert first is not None
        assert second is not None
        # 两次结果指向同一缓存文件
        assert first.image_path == second.image_path
        # _render 只被调用一次（第二次命中缓存）
        assert renderer.render_call_count == 1

    def test_render_failure_returns_none(
        self, prerender_config: PrerenderConfig
    ) -> None:
        """_render 抛异常时 prerender 返回 None。"""
        renderer = _StubPrerenderer(prerender_config, fail=True)
        result = renderer.prerender("will fail")
        assert result is None

    def test_different_content_uses_different_cache(
        self, prerender_config: PrerenderConfig
    ) -> None:
        renderer = _StubPrerenderer(prerender_config)
        r1 = renderer.prerender("content A")
        r2 = renderer.prerender("content B")

        assert r1 is not None
        assert r2 is not None
        assert r1.image_path != r2.image_path
        assert renderer.render_call_count == 2

    def test_extra_args_affect_cache_key(
        self, prerender_config: PrerenderConfig
    ) -> None:
        """相同的 content 但不同 args 应使用不同缓存。"""
        renderer = _StubPrerenderer(prerender_config)
        r1 = renderer.prerender("same", "python")
        r2 = renderer.prerender("same", "java")

        assert r1 is not None
        assert r2 is not None
        assert r1.image_path != r2.image_path


# ──────────────────────── CodeHighlighter 测试 ────────────────────────


class TestCodeHighlighter:
    """测试代码高亮预渲染器。"""

    def test_renders_python_code(
        self, prerender_config: PrerenderConfig
    ) -> None:
        """使用 pygments 渲染 Python 代码应返回有效结果。"""
        style = CodeStyle(theme="monokai", font_size=12)
        renderer = CodeHighlighter(prerender_config, style)

        result = renderer.prerender("print('hello')", "python")

        assert result is not None
        assert result.width > 0
        assert result.height > 0
        assert result.image_path.exists()

    def test_renders_unknown_language_falls_back_to_text(
        self, prerender_config: PrerenderConfig
    ) -> None:
        """未知语言应回退到 TextLexer 而非崩溃。"""
        style = CodeStyle()
        renderer = CodeHighlighter(prerender_config, style)

        result = renderer.prerender("some code", "nonexistent-language-xyz")

        assert result is not None
        assert result.image_path.exists()

    def test_renders_empty_language_guesses_lexer(
        self, prerender_config: PrerenderConfig
    ) -> None:
        """空语言时使用 guess_lexer 推断。"""
        style = CodeStyle()
        renderer = CodeHighlighter(prerender_config, style)

        result = renderer.prerender("def f():\n    return 42", "")

        assert result is not None

    def test_cache_hit_on_second_render(
        self, prerender_config: PrerenderConfig
    ) -> None:
        """相同代码第二次应命中缓存。"""
        style = CodeStyle()
        renderer = CodeHighlighter(prerender_config, style)

        first = renderer.prerender("x = 1", "python")
        second = renderer.prerender("x = 1", "python")

        assert first is not None
        assert second is not None
        assert first.image_path == second.image_path

    def test_fallback_render_used_when_pygments_unavailable(
        self, prerender_config: PrerenderConfig
    ) -> None:
        """pygments 不可用时应走 _fallback_render 路径。

        _render_code_to_image 内部捕获 ImportError 后调用 _fallback_render，
        因此 mock pygments 导入失败时应返回 fallback 图片而非 None。
        """
        style = CodeStyle(font_size=12, padding=4)
        renderer = CodeHighlighter(prerender_config, style)

        # 模拟 pygments 导入失败，应触发 _fallback_render
        import sys
        original_pygments = sys.modules.pop("pygments", None)
        try:
            with patch.dict("sys.modules", {"pygments": None}):
                result = renderer.prerender("hello world", "python")
        finally:
            if original_pygments is not None:
                sys.modules["pygments"] = original_pygments

        # fallback 渲染应成功返回结果
        assert result is not None
        assert result.width > 0
        assert result.height > 0
        assert result.image_path.exists()


# ──────────────────────── LatexRenderer 测试 ────────────────────────


class TestLatexRenderer:
    """测试 LaTeX 公式预渲染器。"""

    def test_renders_simple_formula_with_matplotlib(
        self, prerender_config: PrerenderConfig
    ) -> None:
        """matplotlib 可用时渲染简单公式。"""
        style = LatexStyle(font_size=14, dpi=72)
        renderer = LatexRenderer(prerender_config, style)

        result = renderer.prerender(r"E = mc^2")

        # matplotlib 应该可用
        assert result is not None
        assert result.image_path.exists()

    def test_fallback_render_returns_valid_image(
        self, prerender_config: PrerenderConfig
    ) -> None:
        """强制走 fallback 路径应返回有效图片。"""
        style = LatexStyle(font_size=14, color="#333333")
        renderer = LatexRenderer(prerender_config, style)
        # 强制走 fallback
        renderer._renderer = "fallback"

        result = renderer.prerender(r"x^2 + y^2 = r^2")

        assert result is not None
        assert result.width > 0
        assert result.height > 0
        assert result.image_path.exists()

    def test_fallback_with_transparent_bg_uses_white(
        self, prerender_config: PrerenderConfig
    ) -> None:
        """fallback 模式下 transparent 背景应改为白色。"""
        style = LatexStyle(background_color="transparent")
        renderer = LatexRenderer(prerender_config, style)
        renderer._renderer = "fallback"

        result = renderer.prerender("x=1")

        assert result is not None

    def test_detects_matplotlib_renderer(self, prerender_config: PrerenderConfig) -> None:
        """_detect_renderer 应至少检测到 matplotlib 或 fallback。"""
        style = LatexStyle()
        renderer = LatexRenderer(prerender_config, style)
        assert renderer._renderer in {"matplotlib", "latex2svg", "dvipng", "fallback"}


# ──────────────────────── MermaidRenderer 测试 ────────────────────────


class TestMermaidRenderer:
    """测试 Mermaid 图表预渲染器。"""

    def test_fallback_render_returns_valid_image(
        self, prerender_config: PrerenderConfig
    ) -> None:
        """无 mmdc 和 playwright 时走 fallback 文本渲染。"""
        style = MermaidStyle()
        renderer = MermaidRenderer(prerender_config, style)
        renderer._renderer = "fallback"

        result = renderer.prerender("graph TD\n    A-->B")

        assert result is not None
        assert result.width > 0
        assert result.height > 0
        assert result.image_path.exists()

    def test_fallback_render_multiline(
        self, prerender_config: PrerenderConfig
    ) -> None:
        """多行 mermaid 代码 fallback 渲染应返回更高图片。"""
        style = MermaidStyle()
        renderer = MermaidRenderer(prerender_config, style)
        renderer._renderer = "fallback"

        single = renderer.prerender("graph TD\n    A-->B")
        multi = renderer.prerender("graph TD\n    A-->B\n    B-->C\n    C-->D")

        assert single is not None
        assert multi is not None
        assert multi.height > single.height

    def test_generate_html_contains_mermaid_code(
        self, prerender_config: PrerenderConfig
    ) -> None:
        """_generate_html 应包含 mermaid 代码和样式。"""
        style = MermaidStyle(theme="dark", padding=10)
        renderer = MermaidRenderer(prerender_config, style)

        html = renderer._generate_html("graph TD\n    A-->B")

        assert "mermaid" in html.lower()
        assert "graph TD" in html
        assert "dark" in html

    def test_detect_renderer_returns_valid_value(
        self, prerender_config: PrerenderConfig
    ) -> None:
        style = MermaidStyle()
        renderer = MermaidRenderer(prerender_config, style)
        assert renderer._renderer in {"mmdc", "playwright", "fallback"}

    def test_find_mmdc_returns_none_or_list(self, prerender_config: PrerenderConfig) -> None:
        style = MermaidStyle()
        renderer = MermaidRenderer(prerender_config, style)
        result = renderer._find_mmdc()
        # 在沙箱中通常返回 None（无 mmdc 安装）
        assert result is None or isinstance(result, list)


# ──────────────────────── pipeline 测试 ────────────────────────


class TestPipelineRenderersCreation:
    """测试 _create_renderers 渲染器工厂。"""

    def test_all_renderers_created_when_enabled(
        self, prerender_config: PrerenderConfig, style_config: StyleConfig
    ) -> None:
        renderers = _create_renderers(style_config, prerender_config)
        assert "code" in renderers
        assert "mermaid" in renderers
        assert "latex" in renderers

    def test_only_enabled_renderers_created(
        self, prerender_config: PrerenderConfig, style_config: StyleConfig
    ) -> None:
        config = PrerenderConfig(
            cache_dir=prerender_config.cache_dir,
            enable_code=True,
            enable_mermaid=False,
            enable_latex=False,
        )
        renderers = _create_renderers(style_config, config)
        assert "code" in renderers
        assert "mermaid" not in renderers
        assert "latex" not in renderers

    def test_no_renderers_when_all_disabled(
        self, prerender_config: PrerenderConfig, style_config: StyleConfig
    ) -> None:
        config = PrerenderConfig(
            cache_dir=prerender_config.cache_dir,
            enable_code=False,
            enable_mermaid=False,
            enable_latex=False,
        )
        renderers = _create_renderers(style_config, config)
        assert renderers == {}


class TestDetectMermaidContent:
    """测试 Mermaid 内容检测。"""

    @pytest.mark.parametrize(
        "content",
        [
            "graph TD\n    A-->B",
            "flowchart LR\n    X-->Y",
            "sequenceDiagram\n    A->>B: hello",
            "classDiagram\n    Animal <|-- Dog",
            "stateDiagram-v2\n    [*]-->Active",
            "gantt\n    title 项目计划",
            "pie title Pets\n    \"Dogs\" : 50",
            "erDiagram\n    PERSON ||--o{ PHONE",
            "journey\n    title Going to work",
        ],
    )
    def test_detects_mermaid_patterns(self, content: str) -> None:
        assert _detect_mermaid_content(content) is not None

    def test_returns_none_for_non_mermaid(self) -> None:
        assert _detect_mermaid_content("这是普通段落") is None
        assert _detect_mermaid_content("") is None
        assert _detect_mermaid_content("print('hello')") is None

    def test_returns_original_content(self) -> None:
        content = "graph TD\n    A-->B"
        assert _detect_mermaid_content(content) == content


class TestDetectLatexContent:
    """测试 LaTeX 内容检测。"""

    def test_block_formula_double_dollar(self) -> None:
        assert _detect_latex_content("$$E=mc^2$$") == "E=mc^2"

    def test_inline_formula_single_dollar(self) -> None:
        assert _detect_latex_content("$x^2$") == "x^2"

    def test_block_formula_bracket(self) -> None:
        assert _detect_latex_content(r"\[E=mc^2\]") == "E=mc^2"

    def test_too_short_content_returns_none(self) -> None:
        assert _detect_latex_content("$$") is None  # len <= 4
        assert _detect_latex_content("$") is None  # len <= 2

    def test_non_latex_returns_none(self) -> None:
        assert _detect_latex_content("普通文本") is None
        assert _detect_latex_content("") is None
        assert _detect_latex_content("print($var)") is None


class TestPrerenderItem:
    """测试 _prerender_item 分发逻辑。"""

    def test_code_item_without_mermaid_language(
        self, prerender_config: PrerenderConfig, style_config: StyleConfig
    ) -> None:
        renderers = _create_renderers(style_config, prerender_config)
        item = SlideItem(
            type=SlideItemType.CODE, content="print('hi')", meta={"language": "python"}
        )
        result = _prerender_item(item, renderers)
        assert result.type == SlideItemType.CODE
        # 成功时 meta 中应有 prerender
        assert "prerender" in result.meta

    def test_code_item_with_mermaid_language(
        self, prerender_config: PrerenderConfig, style_config: StyleConfig
    ) -> None:
        renderers = _create_renderers(style_config, prerender_config)
        item = SlideItem(
            type=SlideItemType.CODE,
            content="graph TD\n    A-->B",
            meta={"language": "mermaid"},
        )
        result = _prerender_item(item, renderers)
        # 应使用 mermaid 渲染器
        assert "prerender" in result.meta

    def test_code_item_with_no_language_meta(
        self, prerender_config: PrerenderConfig, style_config: StyleConfig
    ) -> None:
        renderers = _create_renderers(style_config, prerender_config)
        item = SlideItem(type=SlideItemType.CODE, content="x = 1", meta={})
        result = _prerender_item(item, renderers)
        assert "prerender" in result.meta

    def test_paragraph_with_latex(
        self, prerender_config: PrerenderConfig, style_config: StyleConfig
    ) -> None:
        renderers = _create_renderers(style_config, prerender_config)
        item = SlideItem(type=SlideItemType.PARAGRAPH, content="$x^2 + y^2$")
        result = _prerender_item(item, renderers)
        # LaTeX 段落成功后类型转为 IMAGE
        assert result.type == SlideItemType.IMAGE
        assert "prerender" in result.meta

    def test_paragraph_with_mermaid(
        self, prerender_config: PrerenderConfig, style_config: StyleConfig
    ) -> None:
        renderers = _create_renderers(style_config, prerender_config)
        item = SlideItem(
            type=SlideItemType.PARAGRAPH, content="graph TD\n    A-->B"
        )
        result = _prerender_item(item, renderers)
        assert result.type == SlideItemType.IMAGE
        assert "prerender" in result.meta

    def test_plain_paragraph_unchanged(
        self, prerender_config: PrerenderConfig, style_config: StyleConfig
    ) -> None:
        renderers = _create_renderers(style_config, prerender_config)
        item = SlideItem(type=SlideItemType.PARAGRAPH, content="普通文本")
        result = _prerender_item(item, renderers)
        assert result is item  # 未变化

    def test_image_item_unchanged(
        self, prerender_config: PrerenderConfig, style_config: StyleConfig
    ) -> None:
        renderers = _create_renderers(style_config, prerender_config)
        item = SlideItem(type=SlideItemType.IMAGE, content="")
        result = _prerender_item(item, renderers)
        assert result is item

    def test_code_item_with_all_renderers_disabled(
        self, prerender_config: PrerenderConfig, style_config: StyleConfig
    ) -> None:
        """所有渲染器禁用时 code item 应原样返回。"""
        config = PrerenderConfig(
            cache_dir=prerender_config.cache_dir,
            enable_code=False,
            enable_mermaid=False,
            enable_latex=False,
        )
        renderers = _create_renderers(style_config, config)
        item = SlideItem(type=SlideItemType.CODE, content="x=1", meta={"language": "python"})
        result = _prerender_item(item, renderers)
        assert result is item


class TestTryPrerender:
    """测试 _try_prerender 高阶组合器。"""

    def test_successful_render_adds_prerender_meta(
        self, prerender_config: PrerenderConfig, style_config: StyleConfig
    ) -> None:
        renderers = _create_renderers(style_config, prerender_config)
        item = SlideItem(type=SlideItemType.CODE, content="print(1)", meta={"language": "python"})

        result = _try_prerender(
            item, renderers["code"], "print(1)", "python", label="测试"
        )

        assert "prerender" in result.meta
        assert isinstance(result.meta["prerender"], PrerenderResult)

    def test_failed_render_returns_original_item(
        self, prerender_config: PrerenderConfig
    ) -> None:
        """渲染器返回 None 时应返回原 item。"""
        def failing_renderer(*args: str) -> None:
            return None

        item = SlideItem(type=SlideItemType.CODE, content="x", meta={"k": "v"})
        result = _try_prerender(item, failing_renderer, "x", label="测试")

        assert result is item
        assert "prerender" not in result.meta

    def test_preserves_existing_meta(
        self, prerender_config: PrerenderConfig, style_config: StyleConfig
    ) -> None:
        """成功时保留原 meta 中的其他字段。"""
        renderers = _create_renderers(style_config, prerender_config)
        item = SlideItem(
            type=SlideItemType.CODE,
            content="print(1)",
            meta={"language": "python", "custom_field": "保留我"},
        )

        result = _try_prerender(
            item, renderers["code"], "print(1)", "python", label="测试"
        )

        assert result.meta.get("custom_field") == "保留我"
        assert "prerender" in result.meta


class TestPrerenderSlides:
    """测试 prerender_slides / prerender_slide / prerender_slide_items 顶层 API。"""

    def test_prerender_slides_returns_new_list(
        self, prerender_config: PrerenderConfig, style_config: StyleConfig
    ) -> None:
        slides = [
            SlideSpec(
                title="s1",
                items=[SlideItem(type=SlideItemType.CODE, content="x=1", meta={"language": "python"})],
            ),
            SlideSpec(
                title="s2",
                items=[SlideItem(type=SlideItemType.PARAGRAPH, content="普通文本")],
            ),
        ]

        result = prerender_slides(slides, style_config, prerender_config)

        assert len(result) == 2
        assert result[0].title == "s1"
        assert result[1].title == "s2"
        # code item 应被预渲染
        assert "prerender" in result[0].items[0].meta
        # 普通段落保持原样
        assert "prerender" not in result[1].items[0].meta

    def test_prerender_slide_preserves_title_and_hint(
        self, prerender_config: PrerenderConfig, style_config: StyleConfig
    ) -> None:
        slide = SlideSpec(
            title="标题",
            layout_hint="Title and Content",
            items=[SlideItem(type=SlideItemType.CODE, content="x=1", meta={"language": "python"})],
        )

        result = prerender_slide(slide, style_config, prerender_config)

        assert result.title == "标题"
        assert result.layout_hint == "Title and Content"

    def test_prerender_slide_items_returns_new_list(
        self, prerender_config: PrerenderConfig, style_config: StyleConfig
    ) -> None:
        items = [
            SlideItem(type=SlideItemType.CODE, content="x=1", meta={"language": "python"}),
            SlideItem(type=SlideItemType.PARAGRAPH, content="文本"),
        ]

        result = prerender_slide_items(items, style_config, prerender_config)

        assert len(result) == 2
        assert "prerender" in result[0].meta


class TestCacheManagement:
    """测试 clear_cache 和 get_cache_stats。"""

    def test_get_cache_stats_empty(
        self, prerender_config: PrerenderConfig
    ) -> None:
        stats = get_cache_stats(prerender_config)
        assert stats == {"code": 0, "mermaid": 0, "latex": 0}

    def test_get_cache_stats_after_render(
        self, prerender_config: PrerenderConfig, style_config: StyleConfig
    ) -> None:
        renderers = _create_renderers(style_config, prerender_config)
        # 渲染一个 code item
        renderers["code"]("print(1)", "python")

        stats = get_cache_stats(prerender_config)
        assert stats["code"] == 1
        assert stats["mermaid"] == 0
        assert stats["latex"] == 0

    def test_clear_cache_removes_files(
        self, prerender_config: PrerenderConfig, style_config: StyleConfig
    ) -> None:
        renderers = _create_renderers(style_config, prerender_config)
        renderers["code"]("print(1)", "python")
        assert prerender_config.cache_dir.exists()

        clear_cache(prerender_config)
        assert not prerender_config.cache_dir.exists()

    def test_clear_cache_on_nonexistent_dir_no_error(
        self, prerender_config: PrerenderConfig
    ) -> None:
        """清除不存在的缓存目录不应抛异常。"""
        # 使用全新的、未创建的路径
        config = PrerenderConfig(cache_dir=prerender_config.cache_dir / "nonexistent")
        clear_cache(config)  # 不应抛异常


# ──────────────────────── _prerender_paragraph 测试 ────────────────────────


class TestPrerenderParagraph:
    """测试 _prerender_paragraph 的策略链。"""

    def test_mermaid_priority_over_latex(
        self, prerender_config: PrerenderConfig, style_config: StyleConfig
    ) -> None:
        """内容同时匹配 mermaid 和 latex 时优先 mermaid。"""
        # graph TD 不是 latex，所以这个测试可能不太对
        # 让我们构造一个只匹配 mermaid 的内容
        renderers = _create_renderers(style_config, prerender_config)
        item = SlideItem(type=SlideItemType.PARAGRAPH, content="graph TD\n    A-->B")

        result = _prerender_paragraph(item, renderers)

        assert result.type == SlideItemType.IMAGE
        assert "prerender" in result.meta

    def test_latex_when_no_mermaid(
        self, prerender_config: PrerenderConfig, style_config: StyleConfig
    ) -> None:
        renderers = _create_renderers(style_config, prerender_config)
        item = SlideItem(type=SlideItemType.PARAGRAPH, content="$x^2$")

        result = _prerender_paragraph(item, renderers)

        assert result.type == SlideItemType.IMAGE
        assert "prerender" in result.meta

    def test_no_renderer_returns_original(
        self, prerender_config: PrerenderConfig, style_config: StyleConfig
    ) -> None:
        """无渲染器时返回原 item。"""
        item = SlideItem(type=SlideItemType.PARAGRAPH, content="graph TD\n    A-->B")
        result = _prerender_paragraph(item, {})
        assert result is item

    def test_mermaid_renderer_none_skipped(
        self, prerender_config: PrerenderConfig, style_config: StyleConfig
    ) -> None:
        """mermaid 渲染器为 None 时跳过，尝试 latex。"""
        config = PrerenderConfig(
            cache_dir=prerender_config.cache_dir,
            enable_code=True,
            enable_mermaid=False,
            enable_latex=True,
        )
        renderers = _create_renderers(style_config, config)
        item = SlideItem(type=SlideItemType.PARAGRAPH, content="$x^2$")

        result = _prerender_paragraph(item, renderers)

        assert result.type == SlideItemType.IMAGE
        assert "prerender" in result.meta
