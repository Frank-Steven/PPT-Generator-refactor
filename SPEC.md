# PPT-Generator 主题包规范

本文档定义了PPT-Generator主题包的标准规范，确保不同主题包之间的兼容性和一致性。

## 0. 设计原则：语义与视觉分离

本规范遵循**语义与视觉分离**的核心设计原则：

- **语义层**：由 `layouts.yaml` 定义，描述布局的语义角色（如"标题"、"主内容"、"说明文字"），不涉及具体的视觉呈现。
- **视觉层**：由 `template.pptx` 和 `style.yaml` 定义，负责具体的视觉呈现（字体、颜色、位置等）。

这种分离的好处：
1. **内容与样式解耦**：Markdown内容只关心语义，不关心具体样式
2. **主题可互换**：同一内容可以应用不同主题，无需修改内容
3. **布局可扩展**：新增布局只需在 `layouts.yaml` 中定义语义角色
4. **验证自动化**：通过 `layouts.yaml` 可以自动验证模板的完整性

## 1. 主题包目录结构

一个标准的主题包包含以下文件和目录：

```
themes/
└── business-blue/                    # 主题包目录（主题名称）
    ├── manifest.yaml                 # 必需：主题元数据
    ├── layouts.yaml                  # 必需：布局定义
    ├── style.yaml                    # 必需：样式配置
    ├── template.pptx                 # 必需：PPT母版模板
    ├── preview.png                   # 可选：预览图
    ├── fonts/                        # 可选：字体文件目录
    │   ├── font1.ttf
    │   └── font2.ttf
    └── assets/                       # 可选：资源文件目录
        ├── logo.png
        └── background.jpg
```

### 1.1 必需文件说明

| 文件 | 说明 |
|-----|------|
| `manifest.yaml` | 主题包元数据和文件路径映射 |
| `layouts.yaml` | 布局语义定义，描述布局的角色和用途 |
| `style.yaml` | 样式配置，定义代码、表格、图表等元素的样式 |
| `template.pptx` | PowerPoint母版模板，定义视觉呈现 |

### 1.2 目录命名规则

- 主题包目录名使用小写字母和连字符，如 `business-blue`
- 避免使用空格、下划线或特殊字符

## 2. manifest.yaml 规范

`manifest.yaml` 文件定义了主题包的元数据和基本配置。

### 2.1 必需字段

```yaml
name: "Business Blue"                      # 主题显示名称
version: "1.0.0"                           # 版本号，遵循语义化版本
author: "PPT-Generator Team"               # 作者信息
spec_version: "1.0"                        # 规范版本，当前为1.0
```

### 2.2 可选字段

```yaml
description: "商务风格主题，蓝色调，适合企业汇报和演示"  # 主题描述
compatible_generator: ">=1.0.0"            # 兼容的生成器版本

files:                                      # 文件路径映射
  template: "template.pptx"                 # 模板文件路径（相对于主题包目录）
  style: "style.yaml"                       # 样式配置文件路径
  layouts: "layouts.yaml"                   # 布局定义文件路径
  preview: "preview.png"                    # 预览图路径

preview:                                    # 预览配置
  color: "#4472C4"                          # 主题主色调

tags:                                       # 标签列表，用于分类搜索
  - "business"
  - "professional"
  - "blue"
  - "corporate"
```

### 2.3 文件路径规则

- 所有文件路径都是相对于主题包目录的相对路径
- 使用正斜杠 `/` 作为路径分隔符
- 文件路径不区分大小写，但建议保持一致
- 未在 `files` 中指定的文件使用默认文件名（`template.pptx`、`style.yaml`、`layouts.yaml`）

## 3. template.pptx 规范

PPT模板文件定义了主题的视觉呈现。模板中的布局通过 `layouts.yaml` 进行语义描述和验证。

### 3.1 布局与 layouts.yaml 的对应关系

模板中的每个幻灯片布局通过**布局名称**（`name` 字段）与 `layouts.yaml` 中的布局定义关联。`layouts.yaml` 中定义的所有布局必须在模板中存在对应的布局。

### 3.2 占位符命名规范

占位符名称应遵循以下模式：

```
{类型} {序号}
```

示例：
- `Title 1` - 主标题占位符
- `Content Placeholder 2` - 内容占位符
- `Subtitle 2` - 副标题占位符
- `Picture Placeholder 2` - 图片占位符
- `Text Placeholder 3` - 文本占位符

### 3.3 占位符类型映射

| python-pptx 类型 | 规范名称 | 用途 |
|-----------------|---------|------|
| PP_PLACEHOLDER_TYPE.TITLE | title | 主标题 |
| PP_PLACEHOLDER_TYPE.CENTER_TITLE | center_title | 居中标题 |
| PP_PLACEHOLDER_TYPE.SUBTITLE | subtitle | 副标题/说明 |
| PP_PLACEHOLDER_TYPE.BODY | body | 正文内容 |
| PP_PLACEHOLDER_TYPE.OBJECT | object | 对象占位符 |
| PP_PLACEHOLDER_TYPE.PICTURE | picture | 图片占位符 |
| PP_PLACEHOLDER_TYPE.TEXT | text | 文本占位符 |
| PP_PLACEHOLDER_TYPE.FOOTER | footer | 页脚 |
| PP_PLACEHOLDER_TYPE.DATE | date | 日期 |
| PP_PLACEHOLDER_TYPE.SLIDE_NUMBER | slide_number | 幻灯片编号 |

### 3.4 模板设计建议

- 母版中定义统一的字体、颜色、背景
- 每个布局的占位符位置和大小应合理规划
- 占位符名称应与 `layouts.yaml` 中的 `name` 字段保持一致
- 建议保留空白布局（Blank）以支持自定义内容

## 4. layouts.yaml 规范

`layouts.yaml` 是主题包的**布局定义中心**，负责描述每个布局的语义角色、占位符用途和自动应用规则。它是连接内容语义与视觉呈现的桥梁。

### 4.1 整体结构

```yaml
version: "1.0"           # 布局规范版本

defaults:                # 默认布局配置
  default: "title-and-content"
  first_slide: "title-slide"
  section_divider: "section-header"
  # ... 更多默认配置

groups:                  # 布局分组
  title:
    display_name: "标题类"
    description: "用于封面、章节分隔、结束页"
  # ... 更多分组

layouts:                 # 布局定义列表
  - id: "title-slide"
    name: "Title Slide"
    # ... 更多布局属性
```

### 4.2 版本字段

```yaml
version: "1.0"
```

- `version`：布局规范的版本号，当前为 `"1.0"`

### 4.3 默认布局配置（defaults）

定义在不同场景下默认使用的布局ID：

```yaml
defaults:
  default: "title-and-content"       # 默认布局
  first_slide: "title-slide"         # 第一张幻灯片
  section_divider: "section-header"  # 章节分隔页
  content: "title-and-content"       # 普通内容页
  multi_column: "two-content"        # 多栏内容
  media: "content-with-caption"      # 媒体内容
  image: "picture-with-caption"      # 图片内容
  full_width: "blank"                # 全宽内容
```

| 字段 | 说明 | 默认值 |
|-----|------|--------|
| `default` | 通用默认布局 | `title-and-content` |
| `first_slide` | 第一张幻灯片使用的布局 | `title-slide` |
| `section_divider` | 章节分隔页使用的布局 | `section-header` |
| `content` | 普通内容页默认布局 | `title-and-content` |
| `multi_column` | 多栏内容默认布局 | `two-content` |
| `media` | 媒体内容默认布局 | `content-with-caption` |
| `image` | 图片内容默认布局 | `picture-with-caption` |
| `full_width` | 全宽内容默认布局 | `blank` |

### 4.4 布局分组（groups）

将布局按功能分组，便于管理和选择：

```yaml
groups:
  title:
    display_name: "标题类"
    description: "用于封面、章节分隔、结束页"
  content:
    display_name: "内容类"
    description: "用于正文内容展示"
  media:
    display_name: "媒体类"
    description: "用于图片、图表等媒体内容"
  special:
    display_name: "特殊类"
    description: "空白页等特殊布局"
```

每个分组包含以下字段：

| 字段 | 必需 | 说明 |
|-----|------|------|
| `id` | 是 | 分组唯一标识（YAML键名即为id） |
| `display_name` | 否 | 分组显示名称 |
| `description` | 否 | 分组描述 |

### 4.5 布局定义（LayoutDef）

`layouts` 字段是一个布局定义列表，每个布局定义描述一个幻灯片布局的语义信息。

#### 4.5.1 完整示例

```yaml
layouts:
  - id: "title-and-content"
    name: "Title and Content"
    display_name: "标题和内容"
    description: "最常用的内容页布局，包含标题和正文区域"
    group: "content"
    placeholders:
      - index: 0
        type: "title"
        role: "title"
        name: "Title 1"
      - index: 1
        type: "body"
        role: "main-content"
        name: "Content Placeholder 2"
    keywords: ["标题", "内容", "title", "content", "正文"]
    tags: ["content", "default"]
    auto_apply:
      conditions: ["default"]
      priority: 0
```

#### 4.5.2 字段说明

| 字段 | 必需 | 类型 | 说明 |
|-----|------|------|------|
| `id` | 是 | string | 布局唯一标识，使用小写字母和连字符 |
| `name` | 是 | string | 布局名称，必须与 template.pptx 中的布局名称完全一致 |
| `display_name` | 否 | string | 布局显示名称，用于UI展示 |
| `description` | 否 | string | 布局描述 |
| `group` | 否 | string | 所属分组ID，对应 `groups` 中的键 |
| `placeholders` | 否 | list | 占位符定义列表 |
| `keywords` | 否 | list | 关键词列表，用于布局匹配 |
| `tags` | 否 | list | 标签列表，用于分类和筛选 |
| `auto_apply` | 否 | object | 自动应用规则 |

### 4.6 占位符定义（LayoutPlaceholderDef）

描述布局中每个占位符的语义角色：

```yaml
placeholders:
  - index: 0
    type: "title"
    role: "main-title"
    name: "Title 1"
    description: "主标题占位符"
```

| 字段 | 必需 | 类型 | 说明 |
|-----|------|------|------|
| `index` | 是 | int | 占位符索引，从0开始 |
| `type` | 是 | string | 占位符类型（title, body, picture, text, subtitle等） |
| `role` | 否 | string | 语义角色标识，如 `main-title`、`main-content`、`caption` |
| `name` | 否 | string | 占位符名称，应与模板中的占位符名称一致 |
| `description` | 否 | string | 占位符描述 |

### 4.7 自动应用规则（LayoutAutoApply）

定义在什么情况下自动选择此布局：

```yaml
auto_apply:
  conditions: ["default"]
  priority: 0
```

简写形式（仅指定条件列表）：
```yaml
auto_apply: ["first_slide", "last_slide"]
```

| 字段 | 必需 | 类型 | 说明 |
|-----|------|------|------|
| `conditions` | 是 | list | 触发条件列表，满足任一条件即触发 |
| `priority` | 否 | int | 优先级，数值越高优先级越高，默认为0 |

#### 4.7.1 内置条件

| 条件 | 说明 |
|-----|------|
| `default` | 默认布局，当没有其他匹配时使用 |
| `first_slide` | 第一张幻灯片 |
| `last_slide` | 最后一张幻灯片 |
| `section_divider` | 章节分隔页 |
| `content` | 普通内容页 |
| `multi_column` | 多栏内容 |
| `media` | 媒体内容（图表等） |
| `image` | 图片内容 |
| `full_width` | 全宽内容 |

### 4.8 关键词与布局匹配

`keywords` 字段用于基于内容的布局匹配。当幻灯片标题或内容包含关键词时，可能会自动选择匹配的布局。

示例：
```yaml
keywords: ["标题", "封面", "title", "cover", "首页"]
```

- 关键词不区分大小写
- 支持中英文混合
- 匹配优先级由 `auto_apply.priority` 决定

## 5. style.yaml 规范

`style.yaml` 文件定义了主题的样式配置，主要控制代码块、表格、图表等动态生成元素的视觉样式。

> **注意**：布局选择规则已移至 `layouts.yaml` 的 `defaults` 和 `auto_apply` 字段中。

### 5.1 代码块样式

```yaml
code:
  font: "Consolas"              # 代码字体
  font_size: 11                 # 字体大小（磅）
  theme: "monokai"              # 代码高亮主题
  line_numbers: true            # 是否显示行号
  background_color: "#272822"   # 背景颜色
  text_color: "#F8F8F2"         # 文本颜色
  border_radius: 4              # 边框圆角（像素）
  padding: 12                   # 内边距（像素）
  line_height: 1.4              # 行高
```

### 5.2 Mermaid 图表样式

```yaml
mermaid:
  theme: "dark"                 # Mermaid主题
  background_color: "#1a1a1a"   # 背景颜色
  scale: 2                      # 缩放比例
  padding: 10                   # 内边距（像素）
```

### 5.3 LaTeX 公式样式

```yaml
latex:
  font_size: 14                 # 字体大小（磅）
  background_color: "transparent"  # 背景颜色
  dpi: 300                      # 分辨率
  color: "#333333"              # 文本颜色
```

### 5.4 表格样式

```yaml
table:
  font: "微软雅黑"               # 表格字体
  font_size: 10                 # 字体大小（磅）
  header_background: "#4472C4"  # 表头背景色
  header_color: "#FFFFFF"       # 表头文字颜色
  even_row_background: "#F5F5F5"  # 偶数行背景色
  odd_row_background: "#FFFFFF"  # 奇数行背景色
  border_color: "#CCCCCC"       # 边框颜色
  border_width: 1               # 边框宽度（像素）
```

### 5.5 Run级别样式覆盖

```yaml
run_overrides:
  bold:                         # 加粗文本样式
    font: "微软雅黑"
    font_size: 14
    color: "#333333"
  italic:                       # 斜体文本样式
    font: "微软雅黑"
    font_size: 12
    color: "#666666"
  code:                         # 行内代码样式
    font: "Consolas"
    font_size: 10
    background_color: "#F5F5F5"
  link:                         # 链接样式
    font: "微软雅黑"
    color: "#4472C4"
    underline: true
```

每个 `RunStyle` 支持以下字段（均为可选）：

| 字段 | 类型 | 说明 |
|-----|------|------|
| `font` | string | 字体名称 |
| `font_size` | int | 字体大小（磅） |
| `color` | string | 文字颜色 |
| `bold` | bool | 是否加粗 |
| `italic` | bool | 是否斜体 |
| `underline` | bool | 是否下划线 |
| `background_color` | string | 背景颜色 |

## 6. 主题包验证

主题包必须通过以下验证检查。验证逻辑以 `layouts.yaml` 为核心驱动。

### 6.1 结构验证

- [ ] `manifest.yaml` 文件存在且格式正确
- [ ] `layouts.yaml` 文件存在且格式正确
- [ ] `style.yaml` 文件存在且格式正确（不存在时使用默认样式）
- [ ] `template.pptx` 文件存在且可加载
- [ ] 所有在 `manifest.yaml` 的 `files` 中引用的文件路径有效

### 6.2 布局配置验证

- [ ] `layouts.yaml` 中 `version` 字段有效
- [ ] `defaults.default` 指向一个存在的布局ID
- [ ] `defaults` 中所有默认布局ID都能在 `layouts` 中找到
- [ ] `layouts` 列表不为空
- [ ] 每个布局的 `id` 唯一
- [ ] 每个布局的 `name` 不为空
- [ ] 每个布局的 `placeholders` 中 `index` 唯一
- [ ] 每个占位符的 `type` 不为空
- [ ] `groups` 中引用的分组ID有效（如果布局指定了group）

### 6.3 模板验证（layouts.yaml驱动）

模板验证以 `layouts.yaml` 为准，检查模板是否包含所有定义的布局：

- [ ] 模板中包含 `layouts.yaml` 中定义的所有布局（通过 `name` 字段匹配）
- [ ] 每个布局的占位符数量与定义一致（建议验证）
- [ ] 占位符类型匹配（建议验证）

> **验证逻辑**：遍历 `layouts.yaml` 中的每个布局定义，检查其 `name` 字段是否在模板的布局名称中存在。如果模板缺少某个布局，验证失败。

### 6.4 兼容性验证

- [ ] `manifest.yaml` 中 `spec_version` 与当前规范兼容
- [ ] `manifest.yaml` 中 `compatible_generator` 与当前生成器版本兼容（如指定）

## 7. 主题包发布

### 7.1 版本规范

遵循语义化版本控制：

- **主版本号**：不兼容的API变更
- **次版本号**：向后兼容的功能新增
- **修订号**：向后兼容的问题修正

### 7.2 发布流程

1. 更新 `manifest.yaml` 中的版本号
2. 确保所有测试通过
3. 使用验证工具检查主题包完整性
4. 更新 `CHANGELOG.md`（如果存在）
5. 创建版本标签

## 8. 扩展规范

### 8.1 自定义布局

除标准布局外，主题包可以包含自定义布局。自定义布局应：

- 在 `layouts.yaml` 中明确定义
- 使用唯一的 `id` 和 `name`
- 提供清晰的 `description` 和 `keywords`
- 定义合适的 `auto_apply` 规则（如需要）

### 8.2 自定义资源

主题包可以在 `assets/` 目录中包含自定义资源文件，如：

- 公司Logo
- 背景图片
- 图标
- 其他媒体文件

这些资源可以通过样式配置或代码引用使用。

### 8.3 自定义分组

主题包可以定义自定义布局分组，在 `groups` 字段中添加即可：

```yaml
groups:
  custom-group:
    display_name: "自定义分组"
    description: "自定义布局分组"
```

## 附录 A：规范版本历史

| 版本 | 日期 | 变更说明 |
|-----|------|---------|
| 2.0 | 2026-07-04 | 新增 layouts.yaml，布局规则从 style.yaml 迁移，引入语义与视觉分离原则 |
| 1.0 | 2024-01-01 | 初始版本 |

## 附录 B：标准布局参考

以下是标准主题包中定义的布局列表：

| 布局ID | 布局名称 | 分组 | 说明 |
|--------|---------|------|------|
| `title-slide` | Title Slide | title | 标题幻灯片，用于封面、结束页 |
| `title-and-content` | Title and Content | content | 标题和内容，最常用的内容页 |
| `section-header` | Section Header | title | 章节标题，用于章节分隔 |
| `two-content` | Two Content | content | 双栏内容，适合对比展示 |
| `content-with-caption` | Content with Caption | media | 带说明的内容，适合图表 |
| `picture-with-caption` | Picture with Caption | media | 带说明的图片 |
| `blank` | Blank | special | 空白页，适合自定义内容 |

## 附录 C：示例主题包

完整的示例主题包结构：

```
themes/
└── standard/
    ├── manifest.yaml
    ├── layouts.yaml
    ├── style.yaml
    ├── template.pptx
    ├── preview.png
    ├── fonts/
    │   └── MicrosoftYaHei.ttf
    └── assets/
        └── logo.png
```
