"""PPT生成器异常层次结构。

本模块定义了完整的异常层次结构，支持PPT生成管道中的细粒度错误处理。
所有异常都继承自PPTGeneratorError，便于统一捕获处理。

异常层次结构:
    PPTGeneratorError (基类)
        ├── MarkdownParseError    # Markdown解析失败
        ├── TemplateLoadError     # 模板文件加载问题
        ├── SlideRenderingError   # PPT生成失败
        ├── LayoutMatchError      # 布局匹配问题
        ├── InvalidConfigError    # 配置验证失败
        └── MissingFileError      # 缺少必需文件

使用示例:
    from ppt_generator.exceptions import PPTGeneratorError, MarkdownParseError

    try:
        generator.generate()
    except MarkdownParseError as e:
        # 处理Markdown特定错误
    except PPTGeneratorError as e:
        # 统一处理所有生成器错误
"""

from __future__ import annotations


class PPTGeneratorError(Exception):
    """PPT生成器所有失败的基异常。

    这是PPT生成器引发的所有错误的根异常类，可以用作所有生成器相关异常的统一捕获。

    示例:
        try:
            generator.generate()
        except PPTGeneratorError as e:
            print(f"PPT生成失败: {e}")
    """

    pass


class MarkdownParseError(PPTGeneratorError):
    """Markdown解析失败时引发。

    当Markdown解析器遇到无效的Markdown语法、意外的Token结构或其他解析错误时引发此异常。

    示例:
        try:
            parser = MarkdownParser(invalid_markdown)
            slides = parser.parse()
        except MarkdownParseError as e:
            print(f"解析Markdown失败: {e}")
    """

    pass


class TemplateLoadError(PPTGeneratorError):
    """PPT模板无法加载时引发。

    当模板文件缺失、损坏或格式不支持时引发此异常。

    示例:
        try:
            loader = TemplateLoader(corrupted_file)
        except TemplateLoadError as e:
            print(f"加载模板失败: {e}")
    """

    pass


class SlideRenderingError(PPTGeneratorError):
    """幻灯片渲染失败时引发。

    在演示文稿生成阶段，当幻灯片无法正确渲染时引发此异常，包括添加幻灯片、填充内容或保存演示文稿等问题。

    示例:
        try:
            generator.generate()
        except SlideRenderingError as e:
            print(f"渲染幻灯片失败: {e}")
    """

    pass


class LayoutMatchError(PPTGeneratorError):
    """布局匹配失败时引发。

    当无法为幻灯片规格找到合适的布局，或布局匹配逻辑遇到错误时引发此异常。

    示例:
        try:
            matcher.select_layout(slide_spec, layouts)
        except LayoutMatchError as e:
            print(f"匹配布局失败: {e}")
    """

    pass


class InvalidConfigError(PPTGeneratorError):
    """配置无效时引发。

    在模型验证期间，当输入数据未能通过验证检查时引发此异常。常见原因包括必填字段为空、数据类型无效或值超出范围。

    示例:
        try:
            item = SlideItem(type="", content="text")
        except InvalidConfigError as e:
            print(f"配置无效: {e}")
    """

    pass


class EmptySlideError(PPTGeneratorError):
    """幻灯片列表为空时引发。

    当Markdown解析后没有产生任何幻灯片时引发此异常。

    示例:
        try:
            validate_slides([])
        except EmptySlideError as e:
            print(f"幻灯片列表为空: {e}")
    """

    pass


class MissingFileError(PPTGeneratorError):
    """必需文件未找到时引发。

    当指定的文件路径不存在且操作必需该文件时引发此异常。
    不遮蔽Python内置的FileNotFoundError，便于在需要时分别捕获。

    示例:
        try:
            load_theme_pack("missing_dir")
        except MissingFileError as e:
            print(f"文件未找到: {e}")
    """

    pass
