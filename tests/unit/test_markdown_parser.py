"""Markdown解析器单元测试。

本文件测试MarkdownParser的各种解析场景，包括：
- 基本解析功能
- 列表解析
- 空内容处理
- 边界情况
"""

from __future__ import annotations

import pytest

from ppt_generator.core.models import SlideItemType
from ppt_generator.parsers import MarkdownParser


class TestMarkdownParser:
    """测试MarkdownParser类。"""

    def test_parse_basic_markdown(self, sample_markdown: str) -> None:
        """测试解析基本Markdown。"""
        parser = MarkdownParser(sample_markdown)
        slides = parser.parse()

        assert len(slides) == 2
        assert slides[0].title == "幻灯片1"
        assert slides[1].title == "幻灯片2"

    def test_parse_slide_content(self, sample_markdown: str) -> None:
        """测试解析幻灯片内容。"""
        parser = MarkdownParser(sample_markdown)
        slides = parser.parse()

        assert len(slides[0].items) == 2
        assert slides[0].items[0].content == "段落内容1"
        assert slides[0].items[1].content == "段落内容2"

    def test_parse_list_content(self, sample_markdown_with_list: str) -> None:
        """测试解析列表内容。"""
        parser = MarkdownParser(sample_markdown_with_list)
        slides = parser.parse()

        agenda_slide = slides[0]
        assert agenda_slide.title == "议程"
        assert len(agenda_slide.items) == 4
        assert all(item.type == SlideItemType.LIST for item in agenda_slide.items)
        assert agenda_slide.items[0].content == "介绍"
        assert agenda_slide.items[1].content == "方法论"

    def test_parse_empty_markdown(self) -> None:
        """测试解析空Markdown。"""
        parser = MarkdownParser("")
        slides = parser.parse()
        assert len(slides) == 0

    def test_parse_only_whitespace(self) -> None:
        """测试解析仅包含空白的Markdown。"""
        parser = MarkdownParser("   \n\n  ")
        slides = parser.parse()
        assert len(slides) == 0

    def test_parse_single_slide(self) -> None:
        """测试解析单个幻灯片。"""
        markdown = "# 单个幻灯片\n\n内容"
        parser = MarkdownParser(markdown)
        slides = parser.parse()

        assert len(slides) == 1
        assert slides[0].title == "单个幻灯片"
        assert len(slides[0].items) == 1
        assert slides[0].items[0].content == "内容"

    def test_parse_slide_without_content(self) -> None:
        """测试解析没有内容的幻灯片。"""
        markdown = "# 幻灯片标题\n\n# 下一张"
        parser = MarkdownParser(markdown)
        slides = parser.parse()

        assert len(slides) == 2
        assert slides[0].title == "幻灯片标题"
        assert len(slides[0].items) == 0

    def test_parse_heading_with_special_characters(self) -> None:
        """测试解析包含特殊字符的标题。"""
        markdown = "# 标题 with @特殊 &字符\n\n内容"
        parser = MarkdownParser(markdown)
        slides = parser.parse()

        assert slides[0].title == "标题 with @特殊 &字符"

    def test_parse_long_paragraph(self) -> None:
        """测试解析长段落。"""
        long_text = "这是一个非常长的段落，包含很多文字。" * 10
        markdown = f"# 标题\n\n{long_text}"
        parser = MarkdownParser(markdown)
        slides = parser.parse()

        assert len(slides[0].items) == 1
        assert slides[0].items[0].content == long_text
