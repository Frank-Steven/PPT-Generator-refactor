"""命令行接口模块。

本模块提供PPT生成器的命令行界面，支持从命令行调用生成器，
处理参数解析、日志配置和错误处理。

使用方式:
    ppt-generator input.md template.pptx output.pptx --title "我的演示"

命令行参数:
    input: Markdown源文件路径(必需)
    template: PPT模板文件路径(必需)
    output: 输出PPT文件路径(必需)
    --title: 演示文稿标题(可选，默认: "Generated Presentation")
    -v/--verbose: 启用详细日志(可选)

退出码:
    0: 成功
    2: PPT生成器错误
    3: 文件IO错误
    4: 其他意外错误
"""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Sequence
from pathlib import Path

from .core import MissingFileError, PPTGenerator, PPTGeneratorError

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """配置日志记录。

    根据verbose标志设置日志级别和格式。

    参数:
        verbose: 如果为True，设置日志级别为DEBUG；否则为INFO。
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """解析命令行参数。

    使用argparse解析命令行参数，支持位置参数和可选参数。

    参数:
        argv: 命令行参数序列，默认为sys.argv[1:]。

    返回:
        argparse.Namespace对象，包含解析后的参数。

    示例:
        >>> args = parse_args(["input.md", "template.pptx", "output.pptx", "--title", "演示"])
        >>> args.input
        'input.md'
        >>> args.title
        '演示'
    """
    parser = argparse.ArgumentParser(
        prog="ppt-generator",
        description="从结构化Markdown和PPT母版模板创建PowerPoint演示文稿。",
    )
    parser.add_argument(
        "input",
        help="Markdown源文件的路径。",
    )
    parser.add_argument(
        "template",
        help="PPT母版/模板文件的路径。",
    )
    parser.add_argument(
        "output",
        help="输出PowerPoint文件的路径。",
    )
    parser.add_argument(
        "--title",
        default="Generated Presentation",
        help="生成文件的演示文稿标题。",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="启用详细日志记录。",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """命令行入口函数。

    解析命令行参数，配置日志，验证输入文件，读取Markdown内容，
    调用PPTGenerator生成演示文稿，并处理可能的错误。

    参数:
        argv: 命令行参数序列，默认为None(使用sys.argv[1:])。

    返回:
        退出码整数:
            0: 成功
            2: PPTGeneratorError错误
            3: 文件IO错误
            4: 其他意外错误

    示例:
        >>> main(["--help"])
        0
    """
    try:
        args = parse_args(argv)
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 0

    setup_logging(args.verbose)

    try:
        markdown_path = Path(args.input)
        template_path = Path(args.template)
        output_path = Path(args.output)

        if not markdown_path.exists():
            raise MissingFileError(f"输入文件不存在: {markdown_path}")
        if not template_path.exists():
            raise MissingFileError(f"模板文件不存在: {template_path}")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        markdown_text = markdown_path.read_text(encoding="utf-8")
        logger.info(f"从 {markdown_path} 加载Markdown内容")

        generator = PPTGenerator(
            markdown_text=markdown_text,
            template_path=template_path,
            output_path=output_path,
            title=args.title,
        )
        generator.generate()
        logger.info(f"成功将演示文稿保存到 {output_path}")
        print(f"✓ 演示文稿已保存到 {output_path}")
        return 0

    except PPTGeneratorError as e:
        logger.error(f"PPT生成错误: {e}")
        print(f"错误: {e}", file=sys.stderr)
        return 2
    except OSError as e:
        logger.error(f"文件错误: {e}")
        print(f"文件错误: {e}", file=sys.stderr)
        return 3
    except Exception as e:
        logger.exception(f"意外错误: {e}")
        print(f"意外错误: {e}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
