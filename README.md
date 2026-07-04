# PPT-Generator

从结构化Markdown和PPT母版模板生成PowerPoint演示文稿。

## 快速开始

### 安装

```bash
pip install -e .
```

### 使用

**命令行**:
```bash
ppt-generator input.md template.pptx output.pptx --title "我的演示文稿"
```

**编程接口**:
```python
from ppt_generator import PPTGenerator
from pathlib import Path

generator = PPTGenerator(
    markdown_text=open("input.md").read(),
    template_path=Path("template.pptx"),
    output_path=Path("output.pptx"),
    title="我的演示文稿",
)
generator.generate()
```

### 使用主题包

```python
from ppt_generator.themes import load_theme_pack

theme = load_theme_pack(Path("themes/business-blue"))
generator = PPTGenerator(
    markdown_text=open("input.md").read(),
    output_path=Path("output.pptx"),
    theme_pack=theme,
)
generator.generate()
```

## 功能特性

- **函数式架构**: 纯函数管道与IO边界分离
- **Markdown解析**: 支持丰富的Markdown语法
- **智能布局匹配**: 根据内容自动推断布局
- **主题系统**: 支持一键换肤
- **预渲染管线**: 代码高亮、Mermaid图表、LaTeX公式
- **样式配置**: 完整的样式自定义支持

## 文档

完整的文档位于 [docs/index.md](docs/index.md):

| 文档 | 说明 |
|------|------|
| [core/generator.md](docs/core/generator.md) | 生成器核心文档 |
| [core/models.md](docs/core/models.md) | 数据模型文档 |
| [parsers/markdown_parser.md](docs/parsers/markdown_parser.md) | Markdown解析器文档 |
| [matching/layout_matcher.md](docs/matching/layout_matcher.md) | 布局匹配器文档 |
| [prerendering/prerendering.md](docs/prerendering/prerendering.md) | 预渲染管线文档 |
| [rendering/rendering.md](docs/rendering/rendering.md) | 渲染模块文档 |
| [themes/themes.md](docs/themes/themes.md) | 主题系统文档 |
| [SPEC.md](SPEC.md) | 主题包标准规范 |

## 示例

项目提供了完整的样例文件，位于 `examples/` 目录：

```bash
cd examples
python scripts/generate_ppt.py
```

| 示例文件 | 说明 |
|----------|------|
| `product_intro.md` | 产品介绍演示，展示布局提示和富文本格式 |
| `technical_tutorial.md` | Python教程演示，展示代码块和列表 |
| `advanced_features.md` | 高级功能演示，展示代码高亮、Mermaid图表和LaTeX公式（启用预渲染管线） |

## 测试

```bash
pytest -q
pytest --cov=ppt_generator --cov-report=html
```

## 技术栈

- **python-pptx**: PowerPoint文件生成和操作
- **markdown-it-py**: CommonMark兼容的Markdown解析器
- **returns**: 函数式编程库（Result、Maybe Monad）
- **pygments**: 代码语法高亮
- **matplotlib**: LaTeX公式渲染

## 许可证

本项目采用MIT许可证。