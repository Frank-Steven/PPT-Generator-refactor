"""基础单元测试。

本模块包含PPT生成器的基础功能测试，包括包导入、生成器基本方法和CLI帮助命令。
"""

from pathlib import Path

from ppt_generator import PPTGenerator
from ppt_generator.cli import main as cli_main


def test_package_import() -> None:
    """测试包导入是否正常。"""
    assert PPTGenerator is not None


def test_generator_placeholder_methods(tmp_path: Path) -> None:
    """测试生成器的基本占位方法。

    创建一个最小的模板文件，验证生成器能够成功生成PPT文件。
    """
    markdown_text = "# 标题\n\n这是一个测试。"
    output_path = tmp_path / "output.pptx"
    template_path = tmp_path / "template.pptx"

    # 为生成器创建一个最小的模板文件
    from pptx import Presentation

    Presentation().save(str(template_path))

    generator = PPTGenerator(
        markdown_text=markdown_text,
        template_path=template_path,
        output_path=output_path,
        title="测试",
    )
    generator.generate()
    assert output_path.exists()


def test_cli_help_returns_zero() -> None:
    """测试CLI帮助命令返回退出码0。"""
    assert cli_main(["--help"]) == 0
