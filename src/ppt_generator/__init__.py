"""PPT生成器。

从Markdown和PPT模板生成PowerPoint演示文稿的工具库。

## 快速开始

### 基本用法

```python
from ppt_generator import PPTGenerator

generator = PPTGenerator(
    markdown_text="# 标题\\n\\n内容",
    template_path="template.pptx",
    output_path="output.pptx",
)
generator.generate()
```

### 使用主题包

```python
from ppt_generator import generate_ppt_with_theme
from ppt_generator.themes import load_theme_pack

theme_pack = load_theme_pack("themes/business-blue")
result = generate_ppt_with_theme(
    markdown_text="# 标题\\n\\n内容",
    theme_pack=theme_pack,
    output_path="output.pptx",
)
```

### 函数式管道

```python
from ppt_generator import parse_markdown, validate_slides, match_layouts
from ppt_generator.rendering import extract_layouts

layouts = extract_layouts("template.pptx").unwrap()
specs = parse_markdown("# 标题").unwrap()
validated = validate_slides(specs).unwrap()
matched = match_layouts(validated, layouts)
```

## 模块结构

- `ppt_generator.core`: 核心数据模型和生成器主类
- `ppt_generator.parsers`: Markdown解析器
- `ppt_generator.rendering`: PPT渲染和IO操作
- `ppt_generator.prerendering`: 代码高亮、Mermaid图表、LaTeX公式的预渲染管线
- `ppt_generator.themes`: 主题包加载和管理
- `ppt_generator.matching`: 布局匹配器
- `ppt_generator.templates`: 模板加载器
- `ppt_generator.utils`: 通用工具函数
"""

from .core import (
    CodeStyle,
    EmptySlideError,
    InvalidConfigError,
    LatexStyle,
    LayoutAutoApply,
    LayoutConfig,
    LayoutDef,
    LayoutDefaults,
    LayoutGroupDef,
    LayoutMatchError,
    LayoutPlaceholderDef,
    LayoutSpec,
    MarkdownParseError,
    MermaidStyle,
    MissingFileError,
    PaginationConfig,
    PlaceholderSpec,
    PPTGenerator,
    PPTGeneratorError,
    PrerenderConfig,
    PrerenderResult,
    RichRun,
    RunOverrides,
    RunStyle,
    SlideItem,
    SlideItemType,
    SlideRenderingError,
    SlideSpec,
    StyleConfig,
    TableStyle,
    TemplateLoadError,
    ThemePack,
    ThemePackManifest,
    build_slide_specs,
    generate_ppt,
    generate_ppt_with_theme,
    match_layouts,
    parse_markdown,
    render_presentation,
    validate_slides,
)

__version__ = "1.0.0"
__all__ = [
    "PPTGenerator",
    "generate_ppt",
    "generate_ppt_with_theme",
    "parse_markdown",
    "validate_slides",
    "match_layouts",
    "build_slide_specs",
    "render_presentation",
    "SlideItem",
    "SlideItemType",
    "SlideSpec",
    "LayoutSpec",
    "PlaceholderSpec",
    "ThemePack",
    "ThemePackManifest",
    "StyleConfig",
    "CodeStyle",
    "MermaidStyle",
    "LatexStyle",
    "TableStyle",
    "RunStyle",
    "RunOverrides",
    "LayoutConfig",
    "LayoutDef",
    "LayoutGroupDef",
    "LayoutDefaults",
    "LayoutPlaceholderDef",
    "LayoutAutoApply",
    "RichRun",
    "PrerenderResult",
    "PrerenderConfig",
    "PaginationConfig",
    "PPTGeneratorError",
    "MarkdownParseError",
    "TemplateLoadError",
    "SlideRenderingError",
    "LayoutMatchError",
    "InvalidConfigError",
    "EmptySlideError",
    "MissingFileError",
    "__version__",
]
