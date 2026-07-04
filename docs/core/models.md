# 数据模型开发文档

## 1. 概述

本模块定义了PPT生成器的核心数据模型，所有模型均为不可变的冻结dataclass，带有内置验证逻辑。数据模型是整个系统的核心数据结构，在各个模块之间传递数据。

所有模型定义位置：[models.py](file:///C:/Users/frank/Documents/PPT-Generator/src/ppt_generator/core/models.py)

异常定义位置：[exceptions.py](file:///C:/Users/frank/Documents/PPT-Generator/src/ppt_generator/core/exceptions.py)

主题包加载位置：[theme_pack.py](file:///C:/Users/frank/Documents/PPT-Generator/src/ppt_generator/themes/theme_pack.py)

## 2. 模型分类

### 2.1 内容模型

描述幻灯片内容结构的模型：

| 模型 | 说明 |
|------|------|
| SlideItemType | 幻灯片内容项类型枚举 |
| SlideItem | 幻灯片中的单个内容项 |
| SlideSpec | 完整的幻灯片规格 |
| RichRun | 富文本运行对象 |

### 2.2 布局模型

描述模板布局定义的模型：

| 模型 | 说明 |
|------|------|
| PlaceholderSpec | 模板占位符规格（物理） |
| LayoutSpec | 模板布局规格（物理） |
| LayoutPlaceholderDef | 布局占位符定义（语义） |
| LayoutAutoApply | 布局自动应用规则 |
| LayoutDef | 单个布局的完整定义 |
| LayoutGroupDef | 布局分组定义 |
| LayoutDefaults | 默认布局配置 |
| LayoutConfig | 完整的布局配置 |

### 2.3 样式模型

描述各种内容样式配置的模型：

| 模型 | 说明 |
|------|------|
| RunStyle | Run级别样式 |
| RunOverrides | Run级别样式覆盖集合 |
| CodeStyle | 代码块样式配置 |
| MermaidStyle | Mermaid图表样式配置 |
| LatexStyle | LaTeX公式样式配置 |
| TableStyle | 表格样式配置 |
| StyleConfig | 样式配置集合 |

### 2.4 预渲染模型

描述预渲染功能的模型：

| 模型 | 说明 |
|------|------|
| PrerenderConfig | 预渲染配置 |
| PrerenderResult | 预渲染结果 |

### 2.5 主题模型

描述主题包的模型：

| 模型 | 说明 |
|------|------|
| ThemePackManifest | 主题包元数据 |
| ThemePack | 主题包完整定义 |

## 3. 内容模型详细说明

### 3.1 SlideItemType

**定义位置**: [models.py#L17-L36](file:///C:/Users/frank/Documents/PPT-Generator/src/ppt_generator/core/models.py#L17-L36)

幻灯片内容项类型枚举，定义所有支持的内容类型，避免魔法字符串。

**枚举成员**:

| 成员 | 值 | 说明 |
|------|-----|------|
| PARAGRAPH | "paragraph" | 段落文本 |
| LIST | "list" | 列表 |
| IMAGE | "image" | 图片 |
| TABLE | "table" | 表格 |
| CODE | "code" | 代码块 |
| HEADING | "heading" | 标题 |

**使用场景**:
- 标识 SlideItem 的内容类型
- Markdown解析器根据内容类型创建对应枚举值
- 渲染器根据类型选择不同的渲染策略

---

### 3.2 SlideItem

**定义位置**: [models.py#L39-L73](file:///C:/Users/frank/Documents/PPT-Generator/src/ppt_generator/core/models.py#L39-L73)

表示幻灯片中的单个内容项，封装了内容类型、实际内容和元数据，支持灵活处理不同类型的内容。

**属性表**:

| 属性名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| type | SlideItemType | 是 | 内容类型（SlideItemType枚举值） |
| content | str | 是 | 实际内容数据 |
| meta | dict[str, Any] | 否 | 可选元数据字典，用于存储额外属性，默认空字典 |

**验证规则** (`__post_init__`):
- `type` 必须是 `SlideItemType` 枚举实例
- `content` 必须是字符串类型
- 验证失败抛出 `InvalidConfigError`

**使用场景**:
- Markdown解析器将段落文本解析为 `SlideItem(type=SlideItemType.PARAGRAPH, content="...")`
- 列表项解析为 `SlideItem(type=SlideItemType.LIST, content="...")`
- 代码块解析为 `SlideItem(type=SlideItemType.CODE, content="...")`
- 图片解析为 `SlideItem(type=SlideItemType.IMAGE, content="路径", meta={"alt": "..."})`

---

### 3.3 SlideSpec

**定义位置**: [models.py#L76-L114](file:///C:/Users/frank/Documents/PPT-Generator/src/ppt_generator/core/models.py#L76-L114)

指定一个完整的幻灯片规格，表示从Markdown解析的单个幻灯片结构，包含标题、内容项和可选的布局提示。

**属性表**:

| 属性名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| title | str | 是 | 幻灯片标题 |
| items | list[SlideItem] | 否 | 内容项列表，默认为空列表 |
| layout_hint | str \| None | 否 | 布局提示，用于匹配模板布局，默认None |

**验证规则** (`__post_init__`):
- `title` 必须是字符串类型
- `items` 必须是列表类型
- `items` 中的每个元素都必须是 `SlideItem` 实例
- 验证失败抛出 `InvalidConfigError`

**使用场景**:
- 作为 MarkdownParser 的解析结果
- 作为 LayoutMatcher 的输入进行布局匹配
- 作为 PPTGenerator 渲染幻灯片的依据

---

### 3.4 RichRun

**定义位置**: [models.py#L198-L210](file:///C:/Users/frank/Documents/PPT-Generator/src/ppt_generator/core/models.py#L198-L210)

富文本运行对象，直接映射到python-pptx的Run。只携带语义属性，不包含视觉属性，视觉表现由模板和StyleConfig控制。

**属性表**:

| 属性名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| text | str | 是 | 文本内容 |
| bold | bool | 否 | 是否加粗，默认False |
| italic | bool | 否 | 是否斜体，默认False |
| code | bool | 否 | 是否行内代码，默认False |
| link | str \| None | 否 | 链接URL，默认None |
| strikethrough | bool | 否 | 是否删除线，默认False |

**验证规则**: 无 `__post_init__` 验证

**使用场景**:
- 表示Markdown中带有格式的文本片段
- 用于渲染时应用文本格式（粗体、斜体、代码、链接等）
- 作为富文本解析的中间表示

## 4. 布局模型详细说明

### 4.1 PlaceholderSpec

**定义位置**: [models.py#L117-L158](file:///C:/Users/frank/Documents/PPT-Generator/src/ppt_generator/core/models.py#L117-L158)

描述模板布局中的占位符形状，捕获PowerPoint模板布局中占位符形状的元数据，包括名称、类型、索引和形状ID。

**属性表**:

| 属性名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| name | str | 是 | 占位符名称（如 "Title 1"） |
| placeholder_type | str | 是 | 占位符类型（title、body等） |
| index | int | 是 | 占位符索引 |
| shape_id | int | 是 | PowerPoint分配的形状ID |

**验证规则** (`__post_init__`):
- `name` 不能为空字符串
- `index` 必须是非负整数
- `shape_id` 必须是非负整数
- 验证失败抛出 `InvalidConfigError`

**使用场景**:
- TemplateLoader 从PPT模板提取占位符信息
- LayoutMatcher 根据占位符信息进行布局匹配

---

### 4.2 LayoutSpec

**定义位置**: [models.py#L161-L195](file:///C:/Users/frank/Documents/PPT-Generator/src/ppt_generator/core/models.py#L161-L195)

描述模板中可用的幻灯片布局及其占位符，表示从PowerPoint模板提取的完整幻灯片布局定义。

**属性表**:

| 属性名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| name | str | 是 | 布局名称（如 "Title Slide"） |
| placeholders | list[PlaceholderSpec] | 否 | 占位符规格列表，默认为空列表 |

**验证规则** (`__post_init__`):
- `name` 不能为空字符串
- `placeholders` 中的每个元素必须是 `PlaceholderSpec` 实例
- 验证失败抛出 `InvalidConfigError`

**使用场景**:
- TemplateLoader 加载模板后返回的布局列表
- LayoutMatcher 用于匹配幻灯片的布局候选

---

### 4.3 LayoutPlaceholderDef

**定义位置**: [models.py#L285-L303](file:///C:/Users/frank/Documents/PPT-Generator/src/ppt_generator/core/models.py#L285-L303)

布局占位符定义。描述布局中每个占位符的语义角色，而不仅仅是物理位置。

**属性表**:

| 属性名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| index | int | 是 | 占位符索引 |
| type | str | 是 | 占位符类型 |
| role | str \| None | 否 | 语义角色，默认None |
| name | str \| None | 否 | 占位符名称，默认None |
| description | str \| None | 否 | 描述信息，默认None |

**验证规则** (`__post_init__`):
- `index` 必须是非负整数
- `type` 不能为空字符串
- 验证失败抛出 `InvalidConfigError`

**使用场景**:
- 在 layouts.yaml 中定义每个布局的占位符语义
- 用于布局匹配时理解每个占位符的用途
- 关联物理占位符和语义角色

---

### 4.4 LayoutAutoApply

**定义位置**: [models.py#L306-L321](file:///C:/Users/frank/Documents/PPT-Generator/src/ppt_generator/core/models.py#L306-L321)

布局自动应用规则。定义在什么情况下自动选择此布局。

**属性表**:

| 属性名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| conditions | list[str] | 否 | 自动应用条件列表，默认为空列表 |
| priority | int | 否 | 优先级，默认0 |

**验证规则** (`__post_init__`):
- `conditions` 必须是列表类型
- `priority` 必须是整数类型
- 验证失败抛出 `InvalidConfigError`

**使用场景**:
- 在 layouts.yaml 中定义布局的自动匹配规则
- LayoutMatcher 根据条件和优先级自动选择布局

---

### 4.5 LayoutDef

**定义位置**: [models.py#L324-L356](file:///C:/Users/frank/Documents/PPT-Generator/src/ppt_generator/core/models.py#L324-L356)

单个布局的完整定义。包含布局的语义信息、占位符角色定义和匹配规则。template.pptx 中的布局通过 name 字段与此定义关联。

**属性表**:

| 属性名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | str | 是 | 布局唯一标识 |
| name | str | 是 | 布局名称（与模板中布局名对应） |
| display_name | str \| None | 否 | 显示名称，默认None |
| description | str \| None | 否 | 布局描述，默认None |
| group | str \| None | 否 | 所属分组ID，默认None |
| placeholders | list[LayoutPlaceholderDef] | 否 | 占位符定义列表，默认为空列表 |
| keywords | list[str] | 否 | 关键词列表，默认为空列表 |
| tags | list[str] | 否 | 标签列表，默认为空列表 |
| auto_apply | LayoutAutoApply \| None | 否 | 自动应用规则，默认None |

**验证规则** (`__post_init__`):
- `id` 不能为空字符串
- `name` 不能为空字符串
- `placeholders` 必须是列表类型，且每个元素都是 `LayoutPlaceholderDef` 实例
- `keywords` 必须是列表类型
- `tags` 必须是列表类型
- 验证失败抛出 `InvalidConfigError`

**使用场景**:
- 在 layouts.yaml 中定义每个布局的完整信息
- 关联模板中的物理布局和语义定义
- 用于布局匹配和选择

---

### 4.6 LayoutGroupDef

**定义位置**: [models.py#L359-L370](file:///C:/Users/frank/Documents/PPT-Generator/src/ppt_generator/core/models.py#L359-L370)

布局分组定义。

**属性表**:

| 属性名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | str | 是 | 分组唯一标识 |
| display_name | str \| None | 否 | 显示名称，默认None |
| description | str \| None | 否 | 分组描述，默认None |

**验证规则** (`__post_init__`):
- `id` 不能为空字符串
- 验证失败抛出 `InvalidConfigError`

**使用场景**:
- 在 layouts.yaml 中对布局进行分类组织
- 用于UI展示时的布局分组

---

### 4.7 LayoutDefaults

**定义位置**: [models.py#L373-L392](file:///C:/Users/frank/Documents/PPT-Generator/src/ppt_generator/core/models.py#L373-L392)

默认布局配置。定义各种场景下默认使用的布局ID。

**属性表**:

| 属性名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| default | str | 否 | 默认布局，默认 "title-and-content" |
| first_slide | str | 否 | 首页幻灯片布局，默认 "title-slide" |
| section_divider | str | 否 | 节分隔页布局，默认 "section-header" |
| content | str | 否 | 内容页布局，默认 "title-and-content" |
| multi_column | str | 否 | 多列布局，默认 "two-content" |
| media | str | 否 | 媒体布局，默认 "content-with-caption" |
| image | str | 否 | 图片布局，默认 "picture-with-caption" |
| full_width | str | 否 | 全宽布局，默认 "blank" |

**验证规则** (`__post_init__`):
- `default` 不能为空字符串
- 验证失败抛出 `InvalidConfigError`

**使用场景**:
- 定义不同场景下的默认布局选择
- LayoutMatcher 在无法精确匹配时使用默认布局

---

### 4.8 LayoutConfig

**定义位置**: [models.py#L395-L433](file:///C:/Users/frank/Documents/PPT-Generator/src/ppt_generator/core/models.py#L395-L433)

完整的布局配置。从layouts.yaml加载，是主题包的布局定义中心。

**属性表**:

| 属性名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| version | str | 否 | 配置版本，默认 "1.0" |
| defaults | LayoutDefaults | 否 | 默认布局配置，默认LayoutDefaults实例 |
| groups | dict[str, LayoutGroupDef] | 否 | 布局分组字典，默认空字典 |
| layouts | list[LayoutDef] | 否 | 布局定义列表，默认为空列表 |

**验证规则** (`__post_init__`):
- `layouts` 必须是列表类型
- `layouts` 中的每个元素必须是 `LayoutDef` 实例
- 验证失败抛出 `InvalidConfigError`

**方法**:

| 方法名 | 返回类型 | 说明 |
|--------|----------|------|
| get_layout_by_name(name: str) | LayoutDef \| None | 根据布局名称查找布局定义 |
| get_layout_by_id(layout_id: str) | LayoutDef \| None | 根据布局ID查找布局定义 |
| get_default_layout_name(scenario: str = "default") | str | 获取指定场景的默认布局名称 |

**使用场景**:
- 从 layouts.yaml 加载完整的布局配置
- 作为 ThemePack 的布局定义部分
- 提供布局查找和默认布局获取的工具方法

## 5. 样式模型详细说明

### 5.1 RunStyle

**定义位置**: [models.py#L262-L272](file:///C:/Users/frank/Documents/PPT-Generator/src/ppt_generator/core/models.py#L262-L272)

Run级别样式。

**属性表**:

| 属性名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| font | str \| None | 否 | 字体名称，默认None |
| font_size | int \| None | 否 | 字体大小，默认None |
| color | str \| None | 否 | 文字颜色，默认None |
| bold | bool \| None | 否 | 是否加粗，默认None |
| italic | bool \| None | 否 | 是否斜体，默认None |
| underline | bool \| None | 否 | 是否下划线，默认None |
| background_color | str \| None | 否 | 背景颜色，默认None |

**验证规则**: 无 `__post_init__` 验证

**使用场景**:
- 定义特定类型Run的样式覆盖
- 用于 bold、italic、code、link 等语义格式的视觉表现

---

### 5.2 RunOverrides

**定义位置**: [models.py#L275-L282](file:///C:/Users/frank/Documents/PPT-Generator/src/ppt_generator/core/models.py#L275-L282)

Run级别样式覆盖集合。

**属性表**:

| 属性名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| bold | RunStyle | 否 | 粗体样式，默认RunStyle实例 |
| italic | RunStyle | 否 | 斜体样式，默认RunStyle实例 |
| code | RunStyle | 否 | 行内代码样式，默认RunStyle实例 |
| link | RunStyle | 否 | 链接样式，默认RunStyle实例 |

**验证规则**: 无 `__post_init__` 验证

**使用场景**:
- 集中管理各种语义格式的样式覆盖
- 在 style.yaml 中配置不同Run类型的样式

---

### 5.3 CodeStyle

**定义位置**: [models.py#L213-L225](file:///C:/Users/frank/Documents/PPT-Generator/src/ppt_generator/core/models.py#L213-L225)

代码块样式配置。

**属性表**:

| 属性名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| font | str | 否 | 字体，默认 "Consolas" |
| font_size | int | 否 | 字体大小，默认11 |
| theme | str | 否 | 代码高亮主题，默认 "monokai" |
| line_numbers | bool | 否 | 是否显示行号，默认True |
| background_color | str | 否 | 背景颜色，默认 "#272822" |
| text_color | str | 否 | 文字颜色，默认 "#F8F8F2" |
| border_radius | int | 否 | 圆角半径，默认4 |
| padding | int | 否 | 内边距，默认12 |
| line_height | float | 否 | 行高，默认1.4 |

**验证规则**: 无 `__post_init__` 验证

**使用场景**:
- 配置代码块的视觉样式
- 代码预渲染时使用
- 在 style.yaml 中自定义代码块外观

---

### 5.4 MermaidStyle

**定义位置**: [models.py#L228-L235](file:///C:/Users/frank/Documents/PPT-Generator/src/ppt_generator/core/models.py#L228-L235)

Mermaid图表样式配置。

**属性表**:

| 属性名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| theme | str | 否 | 主题，默认 "dark" |
| background_color | str | 否 | 背景颜色，默认 "#1a1a1a" |
| scale | int | 否 | 缩放比例，默认2 |
| padding | int | 否 | 内边距，默认10 |

**验证规则**: 无 `__post_init__` 验证

**使用场景**:
- 配置Mermaid图表的渲染样式
- Mermaid预渲染时使用
- 在 style.yaml 中自定义图表外观

---

### 5.5 LatexStyle

**定义位置**: [models.py#L238-L245](file:///C:/Users/frank/Documents/PPT-Generator/src/ppt_generator/core/models.py#L238-L245)

LaTeX公式样式配置。

**属性表**:

| 属性名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| font_size | int | 否 | 字体大小，默认14 |
| background_color | str | 否 | 背景颜色，默认 "transparent" |
| dpi | int | 否 | 渲染DPI，默认300 |
| color | str | 否 | 文字颜色，默认 "#333333" |

**验证规则**: 无 `__post_init__` 验证

**使用场景**:
- 配置LaTeX公式的渲染样式
- LaTeX预渲染时使用
- 在 style.yaml 中自定义公式外观

---

### 5.6 TableStyle

**定义位置**: [models.py#L248-L259](file:///C:/Users/frank/Documents/PPT-Generator/src/ppt_generator/core/models.py#L248-L259)

表格样式配置。

**属性表**:

| 属性名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| font | str | 否 | 字体，默认 "微软雅黑" |
| font_size | int | 否 | 字体大小，默认10 |
| header_background | str | 否 | 表头背景色，默认 "#4472C4" |
| header_color | str | 否 | 表头文字颜色，默认 "#FFFFFF" |
| even_row_background | str | 否 | 偶数行背景色，默认 "#F5F5F5" |
| odd_row_background | str | 否 | 奇数行背景色，默认 "#FFFFFF" |
| border_color | str | 否 | 边框颜色，默认 "#CCCCCC" |
| border_width | int | 否 | 边框宽度，默认1 |

**验证规则**: 无 `__post_init__` 验证

**使用场景**:
- 配置表格的视觉样式
- 表格渲染时使用
- 在 style.yaml 中自定义表格外观

---

### 5.7 StyleConfig

**定义位置**: [models.py#L436-L444](file:///C:/Users/frank/Documents/PPT-Generator/src/ppt_generator/core/models.py#L436-L444)

样式配置集合。

**属性表**:

| 属性名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| code | CodeStyle | 否 | 代码块样式，默认CodeStyle实例 |
| mermaid | MermaidStyle | 否 | Mermaid图表样式，默认MermaidStyle实例 |
| latex | LatexStyle | 否 | LaTeX公式样式，默认LatexStyle实例 |
| table | TableStyle | 否 | 表格样式，默认TableStyle实例 |
| run_overrides | RunOverrides | 否 | Run级别样式覆盖，默认RunOverrides实例 |

**验证规则**: 无 `__post_init__` 验证

**使用场景**:
- 集中管理所有样式配置
- 作为 ThemePack 的样式配置部分
- 从 style.yaml 加载样式配置

## 6. 预渲染模型详细说明

### 6.1 PrerenderConfig

**定义位置**: [models.py#L457-L466](file:///C:/Users/frank/Documents/PPT-Generator/src/ppt_generator/core/models.py#L457-L466)

预渲染配置。

**属性表**:

| 属性名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| enable_code | bool | 否 | 是否启用代码预渲染，默认True |
| enable_mermaid | bool | 否 | 是否启用Mermaid预渲染，默认True |
| enable_latex | bool | 否 | 是否启用LaTeX预渲染，默认True |
| cache_dir | Path | 否 | 缓存目录，默认 Path(".cache/prerender") |
| dpi | int | 否 | 渲染DPI，默认300 |
| timeout | int | 否 | 超时时间（秒），默认30 |

**验证规则**: 无 `__post_init__` 验证

**使用场景**:
- 配置预渲染功能的开关和参数
- 控制哪些内容类型需要预渲染
- 设置缓存目录和渲染质量

---

### 6.2 PrerenderResult

**定义位置**: [models.py#L447-L454](file:///C:/Users/frank/Documents/PPT-Generator/src/ppt_generator/core/models.py#L447-L454)

预渲染结果。

**属性表**:

| 属性名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| image_path | Path | 是 | 渲染生成的图片路径 |
| width | int | 是 | 图片宽度（像素） |
| height | int | 是 | 图片高度（像素） |
| content_hash | str | 是 | 内容哈希值，用于缓存校验 |

**验证规则**: 无 `__post_init__` 验证

**使用场景**:
- 表示预渲染的输出结果
- 包含渲染图片的路径和尺寸信息
- 用于缓存命中判断（通过content_hash）

## 7. 主题模型详细说明

### 7.1 ThemePackManifest

**定义位置**: [models.py#L469-L489](file:///C:/Users/frank/Documents/PPT-Generator/src/ppt_generator/core/models.py#L469-L489)

主题包元数据。

**属性表**:

| 属性名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| name | str | 是 | 主题包名称 |
| version | str | 是 | 版本号 |
| author | str | 是 | 作者 |
| description | str \| None | 否 | 描述信息，默认None |
| spec_version | str | 否 | 规范版本，默认 "1.0" |
| compatible_generator | str \| None | 否 | 兼容的生成器版本，默认None |
| files | dict[str, str] | 否 | 文件映射字典，默认空字典 |
| preview | dict[str, str] | 否 | 预览图映射，默认空字典 |
| tags | list[str] | 否 | 标签列表，默认为空列表 |

**验证规则** (`__post_init__`):
- `name` 不能为空字符串
- `version` 不能为空字符串
- `author` 不能为空字符串
- 验证失败抛出 `InvalidConfigError`

**使用场景**:
- 存储主题包的基本信息
- 从 manifest.yaml 加载
- 用于主题包列表展示和筛选

---

### 7.2 ThemePack

**定义位置**: [models.py#L492-L505](file:///C:/Users/frank/Documents/PPT-Generator/src/ppt_generator/core/models.py#L492-L505)

主题包。包含PPT母版、样式配置、布局定义和其他资源的完整主题定义。

**属性表**:

| 属性名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| manifest | ThemePackManifest | 是 | 主题包元数据 |
| template_path | Path | 是 | 模板文件路径（template.pptx） |
| style_config | StyleConfig | 是 | 样式配置 |
| layout_config | LayoutConfig | 是 | 布局配置 |
| preview_path | Path \| None | 否 | 预览图路径，默认None |
| fonts_path | Path \| None | 否 | 字体目录路径，默认None |
| assets_path | Path \| None | 否 | 资源目录路径，默认None |

**验证规则**: 无 `__post_init__` 验证

**使用场景**:
- 表示完整的主题包定义
- 由 load_theme_pack() 函数从主题包目录加载
- 作为PPT生成器的主题输入

**加载函数**: [theme_pack.py#L36-L77](file:///C:/Users/frank/Documents/PPT-Generator/src/ppt_generator/themes/theme_pack.py#L36-L77)

## 8. 设计原则

### 8.1 不可变性

所有模型使用 `@dataclass(frozen=True)` 装饰器，确保数据不可变。

**优势**:
- 线程安全：多线程环境下无需担心数据被修改
- 无副作用：函数调用不会意外修改输入数据
- 便于调试和测试：数据状态稳定，易于复现问题
- 可哈希：可以作为字典的键或放入集合中

### 8.2 内置验证

通过 `__post_init__` 方法在初始化时进行验证，确保数据完整性。

**优势**:
- 早期发现错误：在对象创建时就验证，而不是在使用时才发现问题
- 数据完整性保障：确保所有对象都处于有效状态
- 统一的错误处理：所有验证错误都抛出 `InvalidConfigError`
- 自我文档化：验证规则本身就是文档的一部分

### 8.3 类型安全

使用枚举替代魔法字符串，配合Python类型提示提供类型安全。

**优势**:
- 编译器/IDE类型检查：在编码阶段就能发现类型错误
- IDE自动补全：开发体验更好
- 防止拼写错误：枚举值是固定的，不会出现拼写错误
- 代码可读性：语义更清晰

### 8.4 分层设计

模型按照职责分为多个层次，每层关注特定的问题域。

| 层次 | 模型 | 职责 |
|------|------|------|
| 内容层 | SlideSpec, SlideItem, SlideItemType, RichRun | 描述幻灯片内容 |
| 物理布局层 | LayoutSpec, PlaceholderSpec | 描述模板中的物理布局 |
| 语义布局层 | LayoutDef, LayoutPlaceholderDef, LayoutConfig 等 | 描述布局的语义含义 |
| 样式层 | StyleConfig, CodeStyle, TableStyle 等 | 描述各种内容的样式 |
| 预渲染层 | PrerenderConfig, PrerenderResult | 预渲染功能的配置和结果 |
| 主题层 | ThemePack, ThemePackManifest | 完整主题包的定义 |

**优势**:
- 关注点分离：每层只负责自己的职责
- 便于独立扩展：可以独立扩展某一层而不影响其他层
- 清晰的依赖关系：上层依赖下层，下层不依赖上层
- 易于理解和维护：每个模型的职责清晰明确
