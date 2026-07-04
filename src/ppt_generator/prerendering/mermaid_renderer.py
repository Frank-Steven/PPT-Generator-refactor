"""Mermaid图表预渲染器。

使用mermaid-cli或playwright将Mermaid图表渲染为图片。
支持多种图表类型：流程图、时序图、类图、状态图、甘特图等。

预渲染流程:
    1. 检测mermaid-cli或playwright是否可用
    2. 使用可用的工具渲染Mermaid代码
    3. 缓存结果，避免重复渲染

支持的图表类型:
    - flowchart: 流程图
    - sequenceDiagram: 时序图
    - classDiagram: 类图
    - stateDiagram: 状态图
    - gantt: 甘特图
    - pie: 饼图
    - erDiagram: ER图
    - journey: 用户旅程图

依赖检测优先级:
    1. mmdc (mermaid-cli)
    2. playwright + mermaid
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from ..core.models import PrerenderConfig, MermaidStyle
from ..utils import hex_to_rgb, is_windows, safe_run_subprocess
from .base import BasePrerenderer


class MermaidRenderer(BasePrerenderer):
    """Mermaid图表预渲染器。"""

    def __init__(self, config: PrerenderConfig, style: MermaidStyle) -> None:
        """初始化Mermaid渲染器。

        参数:
            config: 预渲染配置。
            style: Mermaid样式配置。
        """
        super().__init__(config, "mermaid")
        self._style = style
        self._renderer = self._detect_renderer()

    def _render(
        self, content: str, output_path: Path, *args: str
    ) -> tuple[int, int] | None:
        """执行Mermaid渲染，返回图片尺寸。"""
        if self._renderer == "mmdc":
            return self._render_with_mmdc(content, output_path)
        elif self._renderer == "playwright":
            return self._render_with_playwright(content, output_path)
        else:
            return self._fallback_render(content, output_path)

    def _detect_renderer(self) -> str:
        """检测可用的渲染器。"""
        mmdc_cmd = self._find_mmdc()
        if mmdc_cmd:
            result = safe_run_subprocess(
                mmdc_cmd + ["--version"],
                self._config.timeout,
                shell=is_windows(),
                label="mmdc检测",
            )
            if result is not None and result.returncode == 0:
                return "mmdc"

        try:
            from playwright import sync_playwright
            return "playwright"
        except ImportError:
            pass

        return "fallback"

    def _is_windows(self) -> bool:
        """判断是否为Windows系统。"""
        return is_windows()

    def _find_mmdc(self) -> list[str] | None:
        """查找mmdc命令。

        在Windows上优先查找.cmd或.ps1脚本。
        """
        import shutil

        if self._is_windows():
            for ext in [".cmd", ".ps1", ".bat", ""]:
                mmdc_path = shutil.which(f"mmdc{ext}")
                if mmdc_path:
                    if ext == ".ps1":
                        return ["powershell", "-ExecutionPolicy", "Bypass", "-File", mmdc_path]
                    return [mmdc_path]
            return None
        else:
            mmdc_path = shutil.which("mmdc")
            return [mmdc_path] if mmdc_path else None

    def _render_with_mmdc(self, mermaid_code: str, output_path: Path) -> tuple[int, int] | None:
        """使用mermaid-cli渲染。"""
        mmdc_cmd = self._find_mmdc()
        if not mmdc_cmd:
            return None

        with tempfile.NamedTemporaryFile(mode="w", suffix=".mmd", delete=False, encoding="utf-8") as f:
            f.write(mermaid_code)
            input_file = f.name

        try:
            args = mmdc_cmd + [
                "-i", input_file,
                "-o", str(output_path),
                "-t", self._style.theme,
                "-b", self._style.background_color,
                "--scale", str(self._style.scale),
            ]

            result = safe_run_subprocess(
                args,
                self._config.timeout,
                shell=is_windows(),
                label="mmdc渲染",
            )

            if result is not None and result.returncode == 0 and output_path.exists():
                with Image.open(str(output_path)) as image:
                    return image.width, image.height
            return None
        finally:
            Path(input_file).unlink(missing_ok=True)

    def _render_with_playwright(self, mermaid_code: str, output_path: Path) -> tuple[int, int] | None:
        """使用playwright渲染。"""
        try:
            from playwright.sync_api import sync_playwright

            html_content = self._generate_html(mermaid_code)

            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page()
                page.set_content(html_content)
                page.wait_for_load_state("networkidle")

                page.screenshot(path=str(output_path))
                browser.close()

                with Image.open(str(output_path)) as image:
                    return image.width, image.height
        except Exception:
            return None

    def _generate_html(self, mermaid_code: str) -> str:
        """生成包含Mermaid图表的HTML页面。"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
            <style>
                body {{ margin: 0; padding: {self._style.padding}px; background: {self._style.background_color}; }}
                .mermaid {{ font-family: sans-serif; }}
            </style>
        </head>
        <body>
            <div class="mermaid">{mermaid_code}</div>
            <script>mermaid.initialize({{ theme: '{self._style.theme}', startOnLoad: true }});</script>
        </body>
        </html>
        """

    def _fallback_render(self, mermaid_code: str, output_path: Path) -> tuple[int, int] | None:
        """回退渲染：显示代码文本。"""
        lines = mermaid_code.split("\n")
        font_size = 12
        line_height = 18
        padding = 20

        font = ImageFont.load_default()

        line_widths = []
        for line in lines:
            bbox = font.getbbox(line)
            line_widths.append(bbox[2] - bbox[0])

        max_width = max(line_widths) if line_widths else 200
        width = max_width + padding * 2
        height = len(lines) * line_height + padding * 2

        image = Image.new("RGB", (width, height), hex_to_rgb(self._style.background_color))
        draw = ImageDraw.Draw(image)

        y = padding
        for line in lines:
            draw.text((padding, y), line, font=font, fill=(200, 200, 200))
            y += line_height

        image.save(str(output_path), format="PNG")
        return width, height
