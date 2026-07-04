"""LaTeX公式预渲染器。

使用matplotlib或latex2svg将LaTeX公式渲染为图片。
支持行内公式和块级公式。

预渲染流程:
    1. 检测可用的LaTeX渲染工具
    2. 使用可用的工具渲染LaTeX公式
    3. 缓存结果，避免重复渲染

支持的工具:
    1. matplotlib: 使用matplotlib的mathtext功能
    2. latex2svg: 需要安装latex2svg包
    3. dvipng: 需要安装TeX发行版

支持的公式类型:
    - 行内公式: $...$
    - 块级公式: $$...$$ 或 \\[...\\]
"""

from __future__ import annotations

import tempfile
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from ..core.models import PrerenderConfig, LatexStyle
from ..utils import hex_to_rgb, safe_run_subprocess
from .base import BasePrerenderer


class LatexRenderer(BasePrerenderer):
    """LaTeX公式预渲染器。"""

    def __init__(self, config: PrerenderConfig, style: LatexStyle) -> None:
        """初始化LaTeX渲染器。

        参数:
            config: 预渲染配置。
            style: LaTeX样式配置。
        """
        super().__init__(config, "latex")
        self._style = style
        self._renderer = self._detect_renderer()

    def _render(
        self, content: str, output_path: Path, *args: str
    ) -> tuple[int, int] | None:
        """执行LaTeX渲染，返回图片尺寸。"""
        if self._renderer == "matplotlib":
            return self._render_with_matplotlib(content, output_path)
        elif self._renderer == "latex2svg":
            return self._render_with_latex2svg(content, output_path)
        elif self._renderer == "dvipng":
            return self._render_with_dvipng(content, output_path)
        else:
            return self._fallback_render(content, output_path)

    def _detect_renderer(self) -> str:
        """检测可用的渲染器。"""
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            return "matplotlib"
        except ImportError:
            pass

        try:
            import latex2svg
            return "latex2svg"
        except ImportError:
            pass

        result = safe_run_subprocess(
            ["dvipng", "--version"],
            self._config.timeout,
            label="dvipng检测",
        )
        if result is not None and result.returncode == 0:
            return "dvipng"

        return "fallback"

    def _render_with_matplotlib(self, latex_code: str, output_path: Path) -> tuple[int, int] | None:
        """使用matplotlib渲染LaTeX公式。"""
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots()
        try:
            ax.text(0.5, 0.5, f"${latex_code}$", fontsize=self._style.font_size, ha="center", va="center")
            ax.axis("off")

            buf = self._style.background_color
            if buf.lower() == "transparent":
                fig.patch.set_alpha(0)
            else:
                fig.patch.set_facecolor(buf)

            plt.savefig(str(output_path), dpi=self._style.dpi, bbox_inches="tight", transparent=True)

            with Image.open(str(output_path)) as image:
                return image.width, image.height
        finally:
            plt.close(fig)

    def _render_with_latex2svg(self, latex_code: str, output_path: Path) -> tuple[int, int] | None:
        """使用latex2svg渲染LaTeX公式。"""
        try:
            import latex2svg

            result = latex2svg.latex2svg(latex_code)
            svg_content = result["svg"]

            with Image.open(BytesIO(svg_content.encode("utf-8"))) as img:
                img.save(str(output_path), format="PNG")

            with Image.open(str(output_path)) as image:
                return image.width, image.height
        except Exception:
            return None

    def _render_with_dvipng(self, latex_code: str, output_path: Path) -> tuple[int, int] | None:
        """使用dvipng渲染LaTeX公式。"""
        tex_content = f"""
        \\documentclass{{standalone}}
        \\usepackage{{amsmath}}
        \\usepackage{{amssymb}}
        \\begin{{document}}
        ${latex_code}$
        \\end{{document}}
        """

        with tempfile.TemporaryDirectory() as tmpdir:
            tex_path = Path(tmpdir) / "formula.tex"
            dvi_path = Path(tmpdir) / "formula.dvi"

            tex_path.write_text(tex_content, encoding="utf-8")

            safe_run_subprocess(
                ["latex", "-output-directory", tmpdir, str(tex_path)],
                self._config.timeout,
                label="latex编译",
            )

            safe_run_subprocess(
                ["dvipng", "-D", str(self._style.dpi), "-o", str(output_path), str(dvi_path)],
                self._config.timeout,
                label="dvipng渲染",
            )

            if output_path.exists():
                with Image.open(str(output_path)) as image:
                    return image.width, image.height

        return None

    def _fallback_render(self, latex_code: str, output_path: Path) -> tuple[int, int] | None:
        """回退渲染：显示公式文本。"""
        font_size = self._style.font_size
        line_height = int(font_size * 1.5)
        padding = 20

        font = ImageFont.load_default()

        bbox = font.getbbox(latex_code)
        text_width = bbox[2] - bbox[0]
        width = text_width + padding * 2
        height = line_height + padding * 2

        bg_color = self._style.background_color
        if bg_color.lower() == "transparent":
            bg_color = "#FFFFFF"

        image = Image.new("RGB", (width, height), hex_to_rgb(bg_color))
        draw = ImageDraw.Draw(image)

        draw.text((padding, padding), latex_code, font=font, fill=hex_to_rgb(self._style.color))

        image.save(str(output_path), format="PNG")
        return width, height
