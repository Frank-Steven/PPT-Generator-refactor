"""代码高亮预渲染器。

使用Pygments库对代码块进行语法高亮，生成带样式的图片。
支持多种编程语言和主题，输出PNG格式图片。

预渲染流程:
    1. 使用Pygments解析代码并生成HTML
    2. 使用Pillow将HTML渲染为图片
    3. 缓存结果，避免重复渲染

支持的语言:
    Python, JavaScript, Java, C++, C#, Go, Rust, TypeScript, HTML, CSS, JSON, YAML等

支持的主题:
    monokai, solarized-dark, solarized-light, github, vs, vs2015等
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from ..core.models import CodeStyle, PrerenderConfig
from ..utils import hex_to_rgb
from .base import BasePrerenderer


class CodeHighlighter(BasePrerenderer):
    """代码高亮预渲染器。"""

    def __init__(self, config: PrerenderConfig, style: CodeStyle) -> None:
        """初始化代码高亮器。

        参数:
            config: 预渲染配置。
            style: 代码样式配置。
        """
        super().__init__(config, "code")
        self._style = style

    def _render(self, content: str, output_path: Path, *args: str) -> tuple[int, int] | None:
        """执行代码渲染，返回图片尺寸。"""
        language = args[0] if args else ""
        image = self._render_code_to_image(content, language)
        image.save(str(output_path), format="PNG")
        return image.width, image.height

    def _render_code_to_image(self, code: str, language: str) -> Image.Image:
        """将代码渲染为图片。"""
        try:
            from pygments import highlight
            from pygments.formatters import ImageFormatter
            from pygments.lexers import get_lexer_by_name, guess_lexer
            from pygments.styles import get_style_by_name

            try:
                lexer = get_lexer_by_name(language) if language else guess_lexer(code)
            except Exception:
                from pygments.lexers import TextLexer

                lexer = TextLexer()

            style = get_style_by_name(self._style.theme)
            formatter = ImageFormatter(
                style=style,
                font_name=self._style.font,
                font_size=self._style.font_size,
                line_numbers=self._style.line_numbers,
                line_number_bg=self._style.background_color,
                bg_color=self._style.background_color,
                padding=self._style.padding,
            )

            result = highlight(code, lexer, formatter)
            with Image.open(BytesIO(result)) as img:
                img.load()
                return img.copy()
        except ImportError:
            return self._fallback_render(code)
        except Exception:
            return self._fallback_render(code)

    def _fallback_render(self, code: str) -> Image.Image:
        """回退渲染：使用简单的文本渲染。"""
        lines = code.split("\n")
        font_size = self._style.font_size
        line_height = int(font_size * self._style.line_height)
        padding = self._style.padding

        try:
            font = ImageFont.truetype(self._style.font, font_size)
        except Exception:
            font = ImageFont.load_default()

        line_widths = []
        for line in lines:
            if line:
                bbox = font.getbbox(line)
                line_widths.append(bbox[2] - bbox[0])
            else:
                line_widths.append(0)

        max_width = max(line_widths) if line_widths else 100
        width = max_width + padding * 2
        height = len(lines) * line_height + padding * 2

        image = Image.new("RGB", (width, height), hex_to_rgb(self._style.background_color))
        draw = ImageDraw.Draw(image)

        y = padding
        for line in lines:
            draw.text((padding, y), line, font=font, fill=hex_to_rgb(self._style.text_color))
            y += line_height

        return image
