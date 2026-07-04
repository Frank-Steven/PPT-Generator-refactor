"""PPT生成器数据模型。

本模块定义了不可变的数据结构，带有内置验证，用于表示幻灯片内容和模板布局规格。
所有模型都是冻结的dataclass，以确保不可变性。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from .exceptions import InvalidConfigError


class SlideItemType(Enum):
    """幻灯片内容项类型枚举。

    定义了所有支持的内容类型，避免魔法字符串。

    成员:
        PARAGRAPH: 段落文本
        LIST: 列表
        IMAGE: 图片
        TABLE: 表格
        CODE: 代码块
        HEADING: 标题
    """

    PARAGRAPH = "paragraph"
    LIST = "list"
    IMAGE = "image"
    TABLE = "table"
    CODE = "code"
    HEADING = "heading"


@dataclass(frozen=True)
class SlideItem:
    """表示幻灯片中的单个内容项。

    封装了内容类型、实际内容和元数据，支持灵活处理不同类型的内容。

    属性:
        type: 内容类型（SlideItemType枚举值）。
        content: 实际内容数据。
        meta: 可选元数据字典，用于存储额外属性。

    抛出:
        InvalidConfigError: 如果type无效或content不是字符串。

    示例:
        >>> item = SlideItem(type=SlideItemType.PARAGRAPH, content="Hello World")
        >>> item.type.value
        'paragraph'
        >>> item.content
        'Hello World'
    """

    type: SlideItemType
    content: str
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """验证SlideItem实例。

        确保type是有效的SlideItemType枚举值，content是字符串。
        """
        if not isinstance(self.type, SlideItemType):
            raise InvalidConfigError(f"SlideItem类型必须是SlideItemType枚举，得到: {type(self.type)}")
        if not isinstance(self.content, str):
            raise InvalidConfigError(f"SlideItem内容必须是字符串，得到: {type(self.content)}")


@dataclass(frozen=True)
class SlideSpec:
    """指定一个完整的幻灯片规格。

    表示从Markdown解析的单个幻灯片结构，包含标题、内容项和可选的布局提示。

    属性:
        title: 幻灯片标题。
        items: 内容项列表。
        layout_hint: 布局提示，用于匹配模板布局。

    抛出:
        InvalidConfigError: 如果title不是字符串或items不是列表。

    示例:
        >>> item = SlideItem(type=SlideItemType.PARAGRAPH, content="内容")
        >>> spec = SlideSpec(title="我的幻灯片", items=[item], layout_hint="Title Slide")
        >>> spec.title
        '我的幻灯片'
        >>> len(spec.items)
        1
    """

    title: str
    items: list[SlideItem] = field(default_factory=list)
    layout_hint: str | None = None

    def __post_init__(self) -> None:
        """验证SlideSpec实例。

        确保title是字符串，items是列表，且items中的每个元素都是SlideItem。
        """
        if not isinstance(self.title, str):
            raise InvalidConfigError(f"SlideSpec标题必须是字符串，得到: {type(self.title)}")
        if not isinstance(self.items, list):
            raise InvalidConfigError(f"SlideSpec内容项必须是列表，得到: {type(self.items)}")
        for idx, item in enumerate(self.items):
            if not isinstance(item, SlideItem):
                raise InvalidConfigError(f"SlideSpec.items[{idx}]必须是SlideItem实例")


@dataclass(frozen=True)
class PlaceholderSpec:
    """描述模板布局中的占位符形状。

    捕获PowerPoint模板布局中占位符形状的元数据，包括名称、类型、索引和形状ID。

    属性:
        name: 占位符名称。
        placeholder_type: 占位符类型。
        index: 占位符索引。
        shape_id: PowerPoint分配的形状ID。

    抛出:
        InvalidConfigError: 如果name为空或index为负数。

    示例:
        >>> placeholder = PlaceholderSpec(
        ...     name="Title 1",
        ...     placeholder_type="title",
        ...     index=0,
        ...     shape_id=1
        ... )
        >>> placeholder.name
        'Title 1'
    """

    name: str
    placeholder_type: str
    index: int
    shape_id: int

    def __post_init__(self) -> None:
        """验证PlaceholderSpec实例。

        确保name不为空，index是非负整数。
        """
        if not self.name:
            raise InvalidConfigError("PlaceholderSpec名称不能为空")
        if self.index < 0:
            raise InvalidConfigError("PlaceholderSpec索引必须是非负整数")
        if self.shape_id < 0:
            raise InvalidConfigError("PlaceholderSpec形状ID必须是非负整数")


@dataclass(frozen=True)
class LayoutSpec:
    """描述模板中可用的幻灯片布局及其占位符。

    表示从PowerPoint模板提取的完整幻灯片布局定义，包含布局名称和所有占位符规格。

    属性:
        name: 布局名称。
        placeholders: 占位符规格列表。

    抛出:
        InvalidConfigError: 如果name为空。

    示例:
        >>> placeholder = PlaceholderSpec(name="Title 1", placeholder_type="title", index=0, shape_id=1)
        >>> layout = LayoutSpec(name="Title Slide", placeholders=[placeholder])
        >>> layout.name
        'Title Slide'
        >>> len(layout.placeholders)
        1
    """

    name: str
    placeholders: list[PlaceholderSpec] = field(default_factory=list)

    def __post_init__(self) -> None:
        """验证LayoutSpec实例。

        确保name不为空，placeholders中的每个元素都是PlaceholderSpec。
        """
        if not self.name:
            raise InvalidConfigError("LayoutSpec名称不能为空")
        for idx, placeholder in enumerate(self.placeholders):
            if not isinstance(placeholder, PlaceholderSpec):
                raise InvalidConfigError(f"LayoutSpec.placeholders[{idx}]必须是PlaceholderSpec实例")


@dataclass(frozen=True)
class RichRun:
    """富文本运行对象，直接映射到python-pptx的Run。

    只携带语义属性，不包含视觉属性，视觉表现由模板和StyleConfig控制。
    """

    text: str
    bold: bool = False
    italic: bool = False
    code: bool = False
    link: str | None = None
    strikethrough: bool = False


@dataclass(frozen=True)
class CodeStyle:
    """代码块样式配置。"""

    font: str = "Consolas"
    font_size: int = 11
    theme: str = "monokai"
    line_numbers: bool = True
    background_color: str = "#272822"
    text_color: str = "#F8F8F2"
    border_radius: int = 4
    padding: int = 12
    line_height: float = 1.4


@dataclass(frozen=True)
class MermaidStyle:
    """Mermaid图表样式配置。"""

    theme: str = "dark"
    background_color: str = "#1a1a1a"
    scale: int = 2
    padding: int = 10


@dataclass(frozen=True)
class LatexStyle:
    """LaTeX公式样式配置。"""

    font_size: int = 14
    background_color: str = "transparent"
    dpi: int = 300
    color: str = "#333333"


@dataclass(frozen=True)
class TableStyle:
    """表格样式配置。"""

    font: str = "微软雅黑"
    font_size: int = 10
    header_background: str = "#4472C4"
    header_color: str = "#FFFFFF"
    even_row_background: str = "#F5F5F5"
    odd_row_background: str = "#FFFFFF"
    border_color: str = "#CCCCCC"
    border_width: int = 1


@dataclass(frozen=True)
class RunStyle:
    """Run级别样式覆盖。"""

    font: str | None = None
    font_size: int | None = None
    color: str | None = None
    bold: bool | None = None
    italic: bool | None = None
    underline: bool | None = None
    background_color: str | None = None


@dataclass(frozen=True)
class RunOverrides:
    """Run级别样式覆盖集合。"""

    bold: RunStyle = field(default_factory=RunStyle)
    italic: RunStyle = field(default_factory=RunStyle)
    code: RunStyle = field(default_factory=RunStyle)
    link: RunStyle = field(default_factory=RunStyle)


@dataclass(frozen=True)
class LayoutPlaceholderDef:
    """布局占位符定义。

    描述布局中每个占位符的语义角色，而不仅仅是物理位置。
    """

    index: int
    type: str
    role: str | None = None
    name: str | None = None
    description: str | None = None

    def __post_init__(self) -> None:
        """验证LayoutPlaceholderDef实例。"""
        if not isinstance(self.index, int) or self.index < 0:
            raise InvalidConfigError("LayoutPlaceholderDef.index必须是非负整数")
        if not self.type or not isinstance(self.type, str):
            raise InvalidConfigError("LayoutPlaceholderDef.type不能为空字符串")


@dataclass(frozen=True)
class LayoutAutoApply:
    """布局自动应用规则。

    定义在什么情况下自动选择此布局。
    """

    conditions: list[str] = field(default_factory=list)
    priority: int = 0

    def __post_init__(self) -> None:
        """验证LayoutAutoApply实例。"""
        if not isinstance(self.conditions, list):
            raise InvalidConfigError("LayoutAutoApply.conditions必须是列表")
        if not isinstance(self.priority, int):
            raise InvalidConfigError("LayoutAutoApply.priority必须是整数")


@dataclass(frozen=True)
class LayoutDef:
    """单个布局的完整定义。

    包含布局的语义信息、占位符角色定义和匹配规则。
    template.pptx 中的布局通过 name 字段与此定义关联。
    """

    id: str
    name: str
    display_name: str | None = None
    description: str | None = None
    group: str | None = None
    placeholders: list[LayoutPlaceholderDef] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    auto_apply: LayoutAutoApply | None = None

    def __post_init__(self) -> None:
        """验证LayoutDef实例。"""
        if not self.id or not isinstance(self.id, str):
            raise InvalidConfigError("LayoutDef.id不能为空字符串")
        if not self.name or not isinstance(self.name, str):
            raise InvalidConfigError("LayoutDef.name不能为空字符串")
        if not isinstance(self.placeholders, list):
            raise InvalidConfigError("LayoutDef.placeholders必须是列表")
        for idx, ph in enumerate(self.placeholders):
            if not isinstance(ph, LayoutPlaceholderDef):
                raise InvalidConfigError(f"LayoutDef.placeholders[{idx}]必须是LayoutPlaceholderDef实例")
        if not isinstance(self.keywords, list):
            raise InvalidConfigError("LayoutDef.keywords必须是列表")
        if not isinstance(self.tags, list):
            raise InvalidConfigError("LayoutDef.tags必须是列表")


@dataclass(frozen=True)
class LayoutGroupDef:
    """布局分组定义。"""

    id: str
    display_name: str | None = None
    description: str | None = None

    def __post_init__(self) -> None:
        """验证LayoutGroupDef实例。"""
        if not self.id or not isinstance(self.id, str):
            raise InvalidConfigError("LayoutGroupDef.id不能为空字符串")


@dataclass(frozen=True)
class LayoutDefaults:
    """默认布局配置。

    定义各种场景下默认使用的布局ID。
    """

    default: str = "title-and-content"
    first_slide: str = "title-slide"
    section_divider: str = "section-header"
    content: str = "title-and-content"
    multi_column: str = "two-content"
    media: str = "content-with-caption"
    image: str = "picture-with-caption"
    full_width: str = "blank"

    def __post_init__(self) -> None:
        """验证LayoutDefaults实例。"""
        if not self.default or not isinstance(self.default, str):
            raise InvalidConfigError("LayoutDefaults.default不能为空字符串")


@dataclass(frozen=True)
class LayoutConfig:
    """完整的布局配置。

    从layouts.yaml加载，是主题包的布局定义中心。
    """

    version: str = "1.0"
    defaults: LayoutDefaults = field(default_factory=LayoutDefaults)
    groups: dict[str, LayoutGroupDef] = field(default_factory=dict)
    layouts: list[LayoutDef] = field(default_factory=list)

    def __post_init__(self) -> None:
        """验证LayoutConfig实例。"""
        if not isinstance(self.layouts, list):
            raise InvalidConfigError("LayoutConfig.layouts必须是列表")
        for idx, layout in enumerate(self.layouts):
            if not isinstance(layout, LayoutDef):
                raise InvalidConfigError(f"LayoutConfig.layouts[{idx}]必须是LayoutDef实例")

    def get_layout_by_name(self, name: str) -> LayoutDef | None:
        """根据布局名称查找布局定义。"""
        for layout in self.layouts:
            if layout.name == name:
                return layout
        return None

    def get_layout_by_id(self, layout_id: str) -> LayoutDef | None:
        """根据布局ID查找布局定义。"""
        for layout in self.layouts:
            if layout.id == layout_id:
                return layout
        return None

    def get_default_layout_name(self, scenario: str = "default") -> str:
        """获取指定场景的默认布局名称。"""
        layout_id = getattr(self.defaults, scenario, self.defaults.default)
        layout = self.get_layout_by_id(layout_id)
        return layout.name if layout else self.defaults.default


@dataclass(frozen=True)
class StyleConfig:
    """样式配置集合。"""

    code: CodeStyle = field(default_factory=CodeStyle)
    mermaid: MermaidStyle = field(default_factory=MermaidStyle)
    latex: LatexStyle = field(default_factory=LatexStyle)
    table: TableStyle = field(default_factory=TableStyle)
    run_overrides: RunOverrides = field(default_factory=RunOverrides)


@dataclass(frozen=True)
class PrerenderResult:
    """预渲染结果。"""

    image_path: Path
    width: int
    height: int
    content_hash: str


@dataclass(frozen=True)
class PrerenderConfig:
    """预渲染配置。"""

    enable_code: bool = True
    enable_mermaid: bool = True
    enable_latex: bool = True
    cache_dir: Path = field(default_factory=lambda: Path(".cache/prerender"))
    dpi: int = 300
    timeout: int = 30


@dataclass(frozen=True)
class ThemePackManifest:
    """主题包元数据。"""

    name: str
    version: str
    author: str
    description: str | None = None
    spec_version: str = "1.0"
    compatible_generator: str | None = None
    files: dict[str, str] = field(default_factory=dict)
    preview: dict[str, str] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.name:
            raise InvalidConfigError("ThemePackManifest名称不能为空")
        if not self.version:
            raise InvalidConfigError("ThemePackManifest版本号不能为空")
        if not self.author:
            raise InvalidConfigError("ThemePackManifest作者不能为空")


@dataclass(frozen=True)
class ThemePack:
    """主题包。

    包含PPT母版、样式配置、布局定义和其他资源的完整主题定义。
    """

    manifest: ThemePackManifest
    template_path: Path
    style_config: StyleConfig
    layout_config: LayoutConfig
    preview_path: Path | None = None
    fonts_path: Path | None = None
    assets_path: Path | None = None