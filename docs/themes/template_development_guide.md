# PPT-Generator 模板开发指南

## 目录

1. [概述](#1-概述)
2. [核心概念](#2-核心概念)
3. [主题包结构](#3-主题包结构)
4. [layouts.yaml 布局定义](#4-layoutsyaml-布局定义)
5. [style.yaml 样式配置](#5-styleyaml-样式配置)
6. [manifest.yaml 元数据](#6-manifestyaml-元数据)
7. [模板制作流程](#7-模板制作流程)
8. [占位符规范](#8-占位符规范)
9. [布局匹配机制](#9-布局匹配机制)
10. [模板验证与测试](#10-模板验证与测试)
11. [最佳实践](#11-最佳实践)
12. [常见问题](#12-常见问题)

---

## 1. 概述

### 1.1 什么是主题包？

PPT-Generator 的主题包（Theme Pack）是一个完整的主题定义单元，包含视觉模板、布局定义、样式配置等所有与主题相关的内容。

主题包的核心设计原则是**语义与视觉分离**：
- `layouts.yaml` - 定义布局的**语义**（是什么、用来做什么、怎么匹配）
- `template.pptx` - 定义布局的**视觉**（长什么样、配色、字体）
- `style.yaml` - 定义内容的**样式**（代码高亮、表格、文本等）

### 1.2 主题包的组成

```
theme-name/
├── manifest.yaml      # 主题元数据（必需）
├── layouts.yaml       # 布局定义（必需）
├── style.yaml         # 样式配置（必需）
├── template.pptx      # PPT模板文件（必需）
├── preview.png        # 预览图（可选）
├── fonts/             # 字体文件（可选）
└── assets/            # 资源文件（可选）
```

### 1.3 设计原则

| 原则 | 说明 |
|------|------|
| **语义与视觉分离** | layouts.yaml 管语义，template.pptx 管视觉 |
| **单一真相来源** | 布局定义以 layouts.yaml 为准，模板只负责呈现 |
| **一致性** | 所有布局使用统一的配色、字体和间距 |
| **可读性** | 确保文本在投影时清晰可读 |
| **可扩展性** | 支持自定义布局，不局限于内置类型 |

---

## 2. 核心概念

### 2.1 布局定义（LayoutDef）

布局定义是 layouts.yaml 中的核心概念，描述一个布局的完整信息：

| 字段 | 说明 |
|------|------|
| id | 布局的唯一标识符（kebab-case） |
| name | 布局名称，与 template.pptx 中的布局名称对应 |
| display_name | 友好显示名称，用于UI展示 |
| description | 布局描述，说明用途和特点 |
| group | 所属分组 |
| placeholders | 占位符定义列表 |
| keywords | 搜索关键词，用于模糊匹配 |
| tags | 标签，用于分类和筛选 |
| auto_apply | 自动应用规则 |

### 2.2 布局分组（LayoutGroup）

对布局进行分类，便于管理和展示：

| 分组 | 说明 | 示例 |
|------|------|------|
| title | 标题类 | 标题幻灯片、章节标题 |
| content | 内容类 | 标题和内容、双栏内容 |
| media | 媒体类 | 带说明的内容、带说明的图片 |
| special | 特殊类 | 空白页 |

### 2.3 占位符语义角色

每个占位符不仅有物理位置，还有语义角色：

| 角色 | 说明 |
|------|------|
| main-title | 主标题 |
| subtitle | 副标题 |
| section-title | 章节标题 |
| main-content | 主要内容区域 |
| left-column | 左栏 |
| right-column | 右栏 |
| caption | 说明文字 |
| picture | 图片区域 |

---

## 3. 主题包结构

### 3.1 完整目录结构

```
my-theme/
├── manifest.yaml      # 主题元数据
├── layouts.yaml       # 布局定义
├── style.yaml         # 样式配置
├── template.pptx      # PPT模板
├── preview.png        # 预览图（可选）
├── fonts/             # 字体文件（可选）
│   └── *.ttf
└── assets/            # 资源文件（可选）
    ├── images/
    └── icons/
```

### 3.2 文件职责划分

| 文件 | 职责 | 是否必需 |
|------|------|----------|
| manifest.yaml | 主题基本信息、版本、作者、文件映射 | ✅ 必需 |
| layouts.yaml | 布局定义、分组、默认值、匹配规则 | ✅ 必需 |
| style.yaml | 代码、表格、文本等内容样式 | ✅ 必需 |
| template.pptx | 视觉模板、母版、布局 | ✅ 必需 |
| preview.png | 主题预览图 | ❌ 可选 |
| fonts/ | 自定义字体 | ❌ 可选 |
| assets/ | 其他资源 | ❌ 可选 |

---

## 4. layouts.yaml 布局定义

`layouts.yaml` 是主题包的**布局定义中心**，所有布局的语义信息都在这里定义。

### 4.1 完整示例

```yaml
version: "1.0"

defaults:
  default: "title-and-content"
  first_slide: "title-slide"
  section_divider: "section-header"
  content: "title-and-content"
  multi_column: "two-content"
  media: "content-with-caption"
  image: "picture-with-caption"
  full_width: "blank"

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

layouts:
  - id: "title-slide"
    name: "Title Slide"
    display_name: "标题幻灯片"
    description: "用于演示文稿封面、章节分隔、结束页"
    group: "title"
    placeholders:
      - index: 0
        type: "title"
        role: "main-title"
        name: "Title 1"
      - index: 1
        type: "subtitle"
        role: "subtitle"
        name: "Subtitle 2"
    keywords: ["标题", "封面", "title", "cover", "首页"]
    tags: ["title", "cover"]
    auto_apply:
      conditions: ["first_slide", "last_slide"]
      priority: 100

  - id: "title-and-content"
    name: "Title and Content"
    display_name: "标题和内容"
    description: "最常用的内容页布局"
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

### 4.2 顶层字段

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| version | string | 否 | 布局规范版本，默认 "1.0" |
| defaults | object | 是 | 默认布局配置 |
| groups | object | 否 | 布局分组定义 |
| layouts | array | 是 | 布局定义列表 |

### 4.3 defaults 默认布局

定义各种场景下默认使用的布局 ID：

| 字段 | 说明 | 默认值 |
|------|------|--------|
| default | 默认布局（找不到匹配时使用） | "title-and-content" |
| first_slide | 第一张幻灯片 | "title-slide" |
| section_divider | 章节分隔页 | "section-header" |
| content | 内容页 | "title-and-content" |
| multi_column | 多栏内容 | "two-content" |
| media | 媒体内容 | "content-with-caption" |
| image | 图片内容 | "picture-with-caption" |
| full_width | 全宽内容 | "blank" |

### 4.4 groups 布局分组

```yaml
groups:
  group-id:
    display_name: "分组显示名"
    description: "分组描述"
```

### 4.5 layouts 布局定义

每个布局的完整字段：

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| id | string | 是 | 布局唯一ID（kebab-case） |
| name | string | 是 | 布局名称，必须与 template.pptx 中的布局名称完全一致 |
| display_name | string | 否 | 友好显示名称 |
| description | string | 否 | 布局描述 |
| group | string | 否 | 所属分组ID |
| placeholders | array | 否 | 占位符定义列表 |
| keywords | array | 否 | 搜索关键词列表，用于模糊匹配 |
| tags | array | 否 | 标签列表 |
| auto_apply | object/array | 否 | 自动应用规则 |

### 4.6 placeholders 占位符定义

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| index | int | 是 | 占位符索引（与模板中对应） |
| type | string | 是 | 占位符类型（title/body/subtitle/picture等） |
| role | string | 否 | 语义角色 |
| name | string | 否 | 占位符名称 |
| description | string | 否 | 说明 |

### 4.7 auto_apply 自动应用规则

可以是对象（带优先级）或数组（仅条件列表）：

```yaml
# 对象形式（带优先级）
auto_apply:
  conditions: ["first_slide", "last_slide"]
  priority: 100

# 数组形式（默认优先级0）
auto_apply: ["default"]
```

---

## 5. style.yaml 样式配置

`style.yaml` 定义各种内容类型的渲染样式。

### 5.1 完整示例

```yaml
code:
  font: "Consolas"
  font_size: 11
  theme: "monokai"
  line_numbers: true
  background_color: "#272822"
  text_color: "#F8F8F2"
  border_radius: 4
  padding: 12
  line_height: 1.4

mermaid:
  theme: "default"
  background_color: "#FFFFFF"
  scale: 2
  padding: 10

latex:
  font_size: 14
  background_color: "transparent"
  dpi: 300
  color: "#1F4E79"

table:
  font: "微软雅黑"
  font_size: 10
  header_background: "#1F4E79"
  header_color: "#FFFFFF"
  even_row_background: "#F5F7FA"
  odd_row_background: "#FFFFFF"
  border_color: "#D0D7DE"
  border_width: 1

run_overrides:
  bold:
    color: "#1F4E79"
    font: "微软雅黑"
  italic:
    color: "#2E75B6"
    font: "微软雅黑"
  code:
    font: "Consolas"
    font_size: 10
    background_color: "#F5F7FA"
    color: "#C7254E"
  link:
    color: "#2E75B6"
    underline: true
    font: "微软雅黑"
```

### 5.2 各部分详解

#### code - 代码块样式

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| font | string | "Consolas" | 代码字体 |
| font_size | int | 11 | 字体大小（磅） |
| theme | string | "monokai" | Pygments 高亮主题 |
| line_numbers | bool | true | 是否显示行号 |
| background_color | string | "#272822" | 背景颜色 |
| text_color | string | "#F8F8F2" | 文本颜色 |
| border_radius | int | 4 | 边框圆角（像素） |
| padding | int | 12 | 内边距（像素） |
| line_height | float | 1.4 | 行高 |

#### mermaid - Mermaid图表样式

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| theme | string | "default" | Mermaid主题 |
| background_color | string | "#FFFFFF" | 背景颜色 |
| scale | int | 2 | 缩放比例 |
| padding | int | 10 | 内边距（像素） |

#### latex - LaTeX公式样式

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| font_size | int | 14 | 字体大小（磅） |
| background_color | string | "transparent" | 背景颜色 |
| dpi | int | 300 | 分辨率 |
| color | string | "#333333" | 文本颜色 |

#### table - 表格样式

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| font | string | "微软雅黑" | 表格字体 |
| font_size | int | 10 | 字体大小（磅） |
| header_background | string | "#4472C4" | 表头背景色 |
| header_color | string | "#FFFFFF" | 表头文字颜色 |
| even_row_background | string | "#F5F5F5" | 偶数行背景色 |
| odd_row_background | string | "#FFFFFF" | 奇数行背景色 |
| border_color | string | "#CCCCCC" | 边框颜色 |
| border_width | int | 1 | 边框宽度（像素） |

#### run_overrides - Run级别样式

支持的类型：`bold`、`italic`、`code`、`link`

每个类型可设置：

| 字段 | 类型 | 说明 |
|------|------|------|
| font | string | 字体名称 |
| font_size | int | 字体大小（磅） |
| color | string | 文字颜色 |
| bold | bool | 是否加粗 |
| italic | bool | 是否斜体 |
| underline | bool | 是否下划线 |
| background_color | string | 背景颜色 |

---

## 6. manifest.yaml 元数据

`manifest.yaml` 定义主题包的基本信息和文件映射。

### 6.1 完整示例

```yaml
name: "My Theme"
version: "1.0.0"
author: "Your Name"
description: "主题描述"
spec_version: "1.0"
compatible_generator: ">=1.0.0"

files:
  template: "template.pptx"
  style: "style.yaml"
  layouts: "layouts.yaml"
  preview: "preview.png"

preview:
  color: "#1F4E79"

tags:
  - "business"
  - "modern"
  - "blue"
```

### 6.2 字段说明

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| name | string | 是 | 主题显示名称 |
| version | string | 是 | 版本号，建议语义化版本 |
| author | string | 是 | 作者或团队名称 |
| description | string | 否 | 主题描述 |
| spec_version | string | 否 | 主题包规范版本 |
| compatible_generator | string | 否 | 兼容的生成器版本 |
| files | object | 是 | 文件路径映射 |
| preview | object | 否 | 预览配置 |
| tags | array | 否 | 标签列表 |

### 6.3 files 文件映射

| 字段 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| template | 是 | "template.pptx" | 模板文件路径 |
| style | 是 | "style.yaml" | 样式配置路径 |
| layouts | 是 | "layouts.yaml" | 布局定义路径 |
| preview | 否 | - | 预览图路径 |

---

## 7. 模板制作流程

### 7.1 方法一：使用 PowerPoint 手动制作（推荐）

#### 步骤 1：规划布局

在动手之前，先规划好需要哪些布局：

1. 列出需要的布局
2. 为每个布局确定 ID 和名称
3. 设计每个布局的占位符位置
4. 编写 layouts.yaml 的初稿

#### 步骤 2：创建模板文件

1. 打开 PowerPoint
2. 新建空白演示文稿
3. 进入「视图」→「幻灯片母版」
4. 设置幻灯片尺寸（推荐 16:9：13.33 x 7.5 英寸）

#### 步骤 3：设计母版

1. 设置背景颜色或图片
2. 添加公司Logo、页眉页脚
3. 设置主题字体和颜色
4. 确保公共元素在母版中

#### 步骤 4：设计布局

对每个布局：

1. 选择左侧布局缩略图
2. 调整占位符的位置和大小
3. 添加布局特有的装饰元素
4. 重命名布局（右键 → 重命名布局）

> **重要**：布局名称必须与 `layouts.yaml` 中的 `name` 字段完全一致（区分大小写）。

#### 步骤 5：保存模板

1. 退出母版视图
2. 删除所有示例幻灯片
3. 另存为 `.pptx` 格式

### 7.2 方法二：基于现有模板修改

最简单的方法是复制并修改内置主题：

```bash
# 复制标准主题
cp -r themes/standard themes/my-theme
```

然后修改：
- `manifest.yaml` - 更新名称、版本、作者等
- `layouts.yaml` - 添加/修改布局定义
- `style.yaml` - 调整样式
- `template.pptx` - 在 PowerPoint 中修改视觉

### 7.3 方法三：程序化生成

适用于需要批量生成或自动化更新的场景。

```python
from pptx import Presentation
from pptx.util import Inches

def create_template(output_path):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    
    # ... 自定义逻辑 ...
    
    prs.save(str(output_path))
```

---

## 8. 占位符规范

### 8.1 占位符类型

| 类型 | 说明 | 常见用途 |
|------|------|----------|
| title | 标题占位符 | 主标题、章节标题 |
| body | 正文占位符 | 主要内容、列表 |
| subtitle | 副标题占位符 | 副标题、说明文字 |
| picture | 图片占位符 | 图片展示 |
| table | 表格占位符 | 表格内容 |
| object | 对象占位符 | 图表、媒体等 |
| center_title | 居中标题 | 章节标题页 |

### 8.2 语义角色建议

为占位符定义语义角色，使布局更具可扩展性：

| 布局 | 占位符索引 | 建议角色 |
|------|-----------|----------|
| Title Slide | 0 | main-title |
| Title Slide | 1 | subtitle |
| Title and Content | 0 | title |
| Title and Content | 1 | main-content |
| Two Content | 0 | title |
| Two Content | 1 | left-column |
| Two Content | 2 | right-column |
| Picture with Caption | 0 | title |
| Picture with Caption | 1 | picture |
| Picture with Caption | 2 | caption |

### 8.3 命名建议

占位符名称虽然不影响功能，但良好的命名可以提高可维护性：

```
Title 1                   → 第一个标题占位符
Content Placeholder 2     → 第二个内容占位符
Text Placeholder 3        → 第三个文本占位符
Picture Placeholder 4     → 第四个图片占位符
```

---

## 9. 布局匹配机制

### 9.1 匹配优先级

布局匹配器按照以下优先级选择布局：

1. **精确匹配**：布局提示与布局名称完全一致
2. **关键词模糊匹配**：根据 layouts.yaml 中的 keywords 计算匹配分数
3. **默认布局**：使用 defaults.default 指定的布局

### 9.2 关键词匹配算法

每个布局有一个关键词列表，匹配时：

1. 将布局提示转为小写
2. 对每个布局，计算有多少个关键词出现在提示中
3. 选择匹配关键词最多的布局
4. 如果分数相同，优先选择列表中靠前的布局

### 9.3 指定布局的方式

#### 方式一：HTML注释（推荐）

```markdown
<!-- layout: Title Slide -->
# 幻灯片标题
内容...
```

#### 方式二：模糊匹配

```markdown
<!-- layout: 双栏 -->
# 双栏内容
```

匹配器会根据关键词自动选择 "Two Content" 布局。

---

## 10. 模板验证与测试

### 10.1 自动验证

加载主题包时会自动验证：

```python
from ppt_generator.themes import load_theme_pack
from pathlib import Path

theme = load_theme_pack(Path("themes/my-theme"))
# 如果验证失败，会抛出异常
```

**验证内容**：
- layouts.yaml 中定义的布局，模板中是否都存在
- manifest.yaml 必需字段是否完整
- style.yaml 格式是否正确

### 10.2 手动检查清单

#### layouts.yaml 检查

- [ ] 所有布局都有唯一的 id
- [ ] 所有布局的 name 与模板中的布局名称完全一致
- [ ] defaults 中引用的布局 ID 都存在
- [ ] placeholders 中的 index 与模板对应
- [ ] keywords 包含中英文关键词

#### template.pptx 检查

- [ ] 包含 layouts.yaml 中定义的所有布局
- [ ] 布局名称拼写正确（区分大小写）
- [ ] 占位符索引与定义一致
- [ ] 占位符类型与定义一致

#### 视觉一致性检查

- [ ] 所有布局使用统一的配色
- [ ] 标题位置在各布局中一致
- [ ] 页眉页脚一致
- [ ] 字体统一

### 10.3 测试建议

创建测试用的 Markdown，覆盖所有布局：

```markdown
<!-- layout: Title Slide -->
# 测试所有布局

<!-- layout: Title and Content -->
# 标题和内容
内容...

<!-- layout: Section Header -->
# 章节标题

<!-- layout: Two Content -->
# 双栏内容
左栏
---
右栏

<!-- ... 更多布局 ... -->
```

---

## 11. 最佳实践

### 11.1 layouts.yaml 最佳实践

1. **ID 使用 kebab-case**
   ```yaml
   id: "title-slide"      # ✅ 好
   id: "TitleSlide"       # ❌ 不好
   id: "title_slide"      # ⚠️ 可以但不推荐
   ```

2. **名称与模板完全一致**
   - 区分大小写
   - 空格和特殊字符要完全匹配

3. **关键词要丰富**
   - 包含中英文
   - 包含同义词
   - 包含常见的用户输入

4. **合理设置默认布局**
   - default 应该是最通用的布局
   - 确保所有 defaults 引用的布局都存在

### 11.2 模板设计最佳实践

1. **从母版开始**
   - 公共元素放在母版中
   - 布局只放布局特有的元素

2. **使用参考线**
   - 打开 PowerPoint 的参考线
   - 确保元素对齐

3. **预留足够空间**
   - 占位符不要太满
   - 考虑不同长度的内容

4. **考虑投影效果**
   - 对比度要足够
   - 字体不要太小

### 11.3 主题包开发流程建议

1. 先写 `layouts.yaml`，定义清楚布局的语义
2. 再做 `template.pptx`，实现视觉
3. 调整 `style.yaml`，优化内容样式
4. 最后完善 `manifest.yaml` 和预览图

---

## 12. 常见问题

### 12.1 layouts.yaml 相关

**Q: layouts.yaml 和 template.pptx 不一致怎么办？**

A: 系统会验证两者的一致性。如果 layouts.yaml 中定义了某个布局，但模板中没有，会抛出 `InvalidConfigError`。

**Q: 可以自定义布局吗？**

A: 可以。除了标准的7种布局，你可以添加任意数量的自定义布局。只需在 layouts.yaml 中定义，并确保模板中有对应名称的布局。

**Q: 布局名称必须是英文吗？**

A: 布局名称可以是任何字符串，但建议使用英文以保持一致性。显示名称（display_name）可以用中文。

### 12.2 模板相关

**Q: 模板文件太大怎么办？**

A: 尝试：
1. 压缩模板中的图片
2. 减少装饰元素
3. 不嵌入字体

**Q: 如何处理自定义字体？**

A: 可以将字体文件放在主题包的 `fonts/` 目录中。

### 12.3 布局匹配相关

**Q: 模糊匹配不准确怎么办？**

A: 可以：
1. 在 layouts.yaml 中添加更多关键词
2. 调整关键词的权重（未来版本支持）
3. 使用精确的布局名称

**Q: 如何指定第一张幻灯片用什么布局？**

A: 在 layouts.yaml 的 `defaults.first_slide` 中指定。

---

## 附录

### A. 内置主题参考

| 主题 | 说明 |
|------|------|
| standard | 标准主题，蓝色系商务风格 |
| business-blue | 商务蓝主题，企业风格 |

### B. 相关文件

- [themes.md](themes.md) - 主题系统概览
- 源代码: `src/ppt_generator/themes/`
- 示例主题: `themes/standard/`

### C. 快速命令

**加载主题包**：
```python
from ppt_generator.themes import load_theme_pack
theme = load_theme_pack(Path("themes/my-theme"))
```

**列出所有布局**：
```python
for layout in theme.layout_config.layouts:
    print(f"{layout.id}: {layout.display_name}")
```

**获取默认布局**：
```python
default_name = theme.layout_config.get_default_layout_name("content")
```
