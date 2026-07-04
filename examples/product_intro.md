<!-- layout: Title Slide -->
# PPT生成器

基于Markdown的自动化演示文稿生成工具

<!-- layout: Title and Content -->
# 产品概述

**PPT生成器**是一款基于Markdown的自动化演示文稿生成工具，采用**函数式编程范式**设计。

* 支持丰富的Markdown语法解析
* 智能匹配PPT模板布局
* 批量生成演示文稿
* 命令行与API双接口

<!-- layout: Section Header -->
# 核心功能

<!-- layout: Two Content -->
# 技术特性

## 函数式架构

* **纯函数管道**：解析、验证、匹配完全分离
* **不可变数据**：所有模型使用 `@dataclass(frozen=True)`
* **错误作为值**：使用 `Result` 类型处理错误
* **依赖注入**：支持自定义解析器和匹配器

## 完整的错误处理

* 完整的异常层次结构
* 铁路式错误传播
* 优雅的降级处理
* 详细的错误日志

<!-- layout: Content with Caption -->
# 布局匹配

系统能够根据内容自动推断最合适的布局：

* **标题页**：第一张幻灯片自动使用 Title Slide 布局
* **章节标题**：使用 Section Header 布局
* **内容页**：使用 Title and Content 布局
* **多栏内容**：使用 Two Content 布局

<!-- layout: Picture with Caption -->
# 预渲染管线

支持代码高亮、Mermaid图表和LaTeX公式的图片预渲染。

```python
def generate_ppt(text, template):
    slide_specs = parse(text)
    layouts = extract(template)
    return render(slide_specs, layouts)
```

<!-- layout: Title and Content -->
# 优势对比

| 对比项 | 传统方式 | PPT生成器 |
|--------|----------|-----------|
| 制作效率 | 低 | **高** |
| 格式统一 | 难 | **易** |
| 版本控制 | 难 | **易** |
| 协作编辑 | 难 | **易** |

<!-- layout: Title Slide -->
# 结语

感谢您使用PPT生成器！

* 项目主页: https://github.com/ppt-generator
* 文档地址: https://ppt-generator.readthedocs.io