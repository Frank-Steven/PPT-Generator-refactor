"""Markdown解析器模块。

本模块负责将结构化的Markdown文本解析为幻灯片规格列表(SlideSpec)。
解析器使用函数式编程风格，通过reduce函数处理Token流，并使用returns.Maybe monad处理可能为空的状态。

支持的Markdown语法:
- 一级标题(#)作为幻灯片标题
- 二级标题(##)作为章节副标题
- 段落作为paragraph类型内容
- 无序列表(*)作为list类型内容
- 有序列表(1.)作为list类型内容
- 代码块(```)作为code类型内容
- 表格作为table类型内容
- 图片(![])作为image类型内容
- 内联格式：加粗(**), 斜体(*), 行内代码(`), 删除线(~~)

自动布局推断:
- 第一张幻灯片: Title Slide
- 章节过渡页(仅标题，无内容): Section Header
- 包含列表项的幻灯片: Title and Content
- 仅包含段落的幻灯片: Title and Content
- 内容较多的幻灯片: Content with Caption
"""

from __future__ import annotations

from collections.abc import Callable
from functools import reduce

from markdown_it import MarkdownIt
from markdown_it.token import Token
from returns.maybe import Maybe

from ..core.models import RichRun, SlideItem, SlideItemType, SlideSpec


def _token_text(token: Token) -> str:
    """从Token中提取文本内容。

    参数:
        token: markdown-it Token对象。

    返回:
        Token中的纯文本内容。
    """
    if token.type == "text":
        return token.content
    return "".join(child.content for child in token.children or [] if child.type == "text")


def _update_or_create(
    slide_maybe: Maybe[SlideSpec],
    updater: Callable[[SlideSpec], SlideSpec],
    fallback_factory: Callable[[], SlideSpec],
) -> Maybe[SlideSpec]:
    """高阶组合器：更新已有幻灯片或创建新幻灯片。

    统一处理 _reducer 中重复的 `current_slide.map(updater).or_else_call(fallback)` 模式。

    参数:
        slide_maybe: 当前幻灯片的 Maybe 值。
        updater: 接收已有幻灯片并返回更新后幻灯片的函数。
        fallback_factory: 当没有当前幻灯片时创建新幻灯片的函数。

    返回:
        包含更新后或新创建幻灯片的 Maybe 值。
    """
    return Maybe.from_value(slide_maybe.map(updater).or_else_call(fallback_factory))


def _parse_inline_runs(token: Token) -> list[RichRun]:
    """解析inline token中的子元素，生成RichRun列表。

    参数:
        token: markdown-it inline Token对象。

    返回:
        RichRun列表，包含语义格式信息。
    """
    runs: list[RichRun] = []

    if not token.children:
        if token.type == "inline":
            return [RichRun(text=token.content)]
        return [RichRun(text=_token_text(token))]

    for child in token.children:
        text = child.content
        bold = False
        italic = False
        code = False
        link: str | None = None
        strikethrough = False

        if child.type == "strong_open":
            bold = True
        elif child.type == "em_open":
            italic = True
        elif child.type == "code_inline":
            code = True
        elif child.type == "s_open":
            strikethrough = True
        elif child.type == "link_open":
            href = child.attrs.get("href") if child.attrs else None
            link = str(href) if href is not None else None
        elif child.type == "text":
            runs.append(
                RichRun(
                    text=text,
                    bold=bold,
                    italic=italic,
                    code=code,
                    link=link,
                    strikethrough=strikethrough,
                )
            )

        if child.children:
            nested_runs = _parse_inline_runs(child)
            for nested_run in nested_runs:
                merged_run = RichRun(
                    text=nested_run.text,
                    bold=nested_run.bold or bold,
                    italic=nested_run.italic or italic,
                    code=nested_run.code or code,
                    link=nested_run.link or link,
                    strikethrough=nested_run.strikethrough or strikethrough,
                )
                runs.append(merged_run)

    return runs


def _is_h1_heading_open(token: Token) -> bool:
    """判断Token是否为一级标题开始标记。

    参数:
        token: markdown-it Token对象。

    返回:
        如果是h1标题开始标记返回True，否则返回False。
    """
    return token.type == "heading_open" and token.tag == "h1"


def _is_h1_heading_close(token: Token) -> bool:
    """判断Token是否为一级标题结束标记。

    参数:
        token: markdown-it Token对象。

    返回:
        如果是h1标题结束标记返回True，否则返回False。
    """
    return token.type == "heading_close" and token.tag == "h1"


def _is_h2_heading_open(token: Token) -> bool:
    """判断Token是否为二级标题开始标记。

    参数:
        token: markdown-it Token对象。

    返回:
        如果是h2标题开始标记返回True，否则返回False。
    """
    return token.type == "heading_open" and token.tag == "h2"


def _is_h2_heading_close(token: Token) -> bool:
    """判断Token是否为二级标题结束标记。

    参数:
        token: markdown-it Token对象。

    返回:
        如果是h2标题结束标记返回True，否则返回False。
    """
    return token.type == "heading_close" and token.tag == "h2"


def _is_inline(token: Token) -> bool:
    """判断Token是否为inline类型。

    参数:
        token: markdown-it Token对象。

    返回:
        如果是inline类型返回True，否则返回False。
    """
    return token.type == "inline"


def _is_list_item_open(token: Token) -> bool:
    """判断Token是否为列表项开始标记。

    参数:
        token: markdown-it Token对象。

    返回:
        如果是列表项开始标记返回True，否则返回False。
    """
    return token.type == "list_item_open"


def _is_list_item_close(token: Token) -> bool:
    """判断Token是否为列表项结束标记。

    参数:
        token: markdown-it Token对象。

    返回:
        如果是列表项结束标记返回True，否则返回False。
    """
    return token.type == "list_item_close"


def _is_code_block_open(token: Token) -> bool:
    """判断Token是否为代码块开始标记。

    参数:
        token: markdown-it Token对象。

    返回:
        如果是代码块开始标记返回True，否则返回False。
    """
    return token.type == "fence"


def _is_table_open(token: Token) -> bool:
    """判断Token是否为表格开始标记。

    参数:
        token: markdown-it Token对象。

    返回:
        如果是表格开始标记返回True，否则返回False。
    """
    return token.type == "table_open"


def _is_table_close(token: Token) -> bool:
    """判断Token是否为表格结束标记。

    参数:
        token: markdown-it Token对象。

    返回:
        如果是表格结束标记返回True，否则返回False。
    """
    return token.type == "table_close"


def _is_image(token: Token) -> bool:
    """判断Token是否为图片标记。

    参数:
        token: markdown-it Token对象。

    返回:
        如果是图片标记返回True，否则返回False。
    """
    return token.type == "image"


def _parse_layout_hint_from_comment(content: str) -> str | None:
    """从HTML注释中解析布局提示。

    参数:
        content: HTML注释内容。

    返回:
        布局提示字符串，如果没有找到则返回None。
    """
    import re

    match = re.search(r"layout:\s*([^\s<][^<]*?)", content, re.IGNORECASE)
    if match:
        hint = match.group(1).strip()
        hint = re.sub(r"[-]+$", "", hint).strip()
        return hint
    return None


def _append_slide(slides: list[SlideSpec], slide: SlideSpec | None) -> list[SlideSpec]:
    """将幻灯片追加到列表中。

    参数:
        slides: 现有幻灯片列表。
        slide: 要添加的幻灯片，如果为None则不添加。

    返回:
        更新后的幻灯片列表。
    """
    return slides + [slide] if slide is not None else slides


def _infer_layout_hint(slide: SlideSpec, is_first: bool) -> str:
    """根据幻灯片内容推断布局提示。

    参数:
        slide: 当前幻灯片规格。
        is_first: 是否为第一张幻灯片。

    返回:
        布局提示字符串。
    """
    if is_first:
        return "Title Slide"

    if not slide.items:
        return "Section Header"

    has_list = any(item.type == SlideItemType.LIST for item in slide.items)
    has_paragraph = any(item.type == SlideItemType.PARAGRAPH for item in slide.items)
    has_code = any(item.type == SlideItemType.CODE for item in slide.items)
    has_table = any(item.type == SlideItemType.TABLE for item in slide.items)
    has_image = any(item.type == SlideItemType.IMAGE for item in slide.items)
    item_count = len(slide.items)

    if item_count >= 6 or has_table or has_image:
        return "Content with Caption"
    elif has_list and has_paragraph or has_list or has_paragraph or has_code:
        return "Title and Content"

    return "Title and Content"


def _add_paragraph_item(slide: SlideSpec, content: str, runs: list[RichRun]) -> SlideSpec:
    """向幻灯片添加段落内容项。

    如果当前幻灯片没有标题，则将内容作为标题；否则作为段落内容。

    参数:
        slide: 当前幻灯片规格。
        content: 要添加的内容。
        runs: RichRun列表。

    返回:
        更新后的幻灯片规格。
    """
    if slide.title == "":
        return SlideSpec(title=content, items=slide.items, layout_hint=slide.layout_hint)
    return SlideSpec(
        title=slide.title,
        items=slide.items
        + [SlideItem(type=SlideItemType.PARAGRAPH, content=content, meta={"runs": runs})],
        layout_hint=slide.layout_hint,
    )


def _add_list_item(slide: SlideSpec, content: str, runs: list[RichRun]) -> SlideSpec:
    """向幻灯片添加列表内容项。

    参数:
        slide: 当前幻灯片规格。
        content: 列表项内容。
        runs: RichRun列表。

    返回:
        更新后的幻灯片规格。
    """
    return SlideSpec(
        title=slide.title,
        items=slide.items
        + [SlideItem(type=SlideItemType.LIST, content=content, meta={"runs": runs})],
        layout_hint=slide.layout_hint,
    )


def _add_code_block_item(slide: SlideSpec, content: str, language: str) -> SlideSpec:
    """向幻灯片添加代码块内容项。

    参数:
        slide: 当前幻灯片规格。
        content: 代码内容。
        language: 代码语言。

    返回:
        更新后的幻灯片规格。
    """
    return SlideSpec(
        title=slide.title,
        items=slide.items
        + [SlideItem(type=SlideItemType.CODE, content=content, meta={"language": language})],
        layout_hint=slide.layout_hint,
    )


def _add_table_item(slide: SlideSpec, content: str, rows: int, cols: int) -> SlideSpec:
    """向幻灯片添加表格内容项。

    参数:
        slide: 当前幻灯片规格。
        content: 表格Markdown内容。
        rows: 行数。
        cols: 列数。

    返回:
        更新后的幻灯片规格。
    """
    return SlideSpec(
        title=slide.title,
        items=slide.items
        + [SlideItem(type=SlideItemType.TABLE, content=content, meta={"rows": rows, "cols": cols})],
        layout_hint=slide.layout_hint,
    )


def _add_image_item(slide: SlideSpec, content: str, src: str, alt: str) -> SlideSpec:
    """向幻灯片添加图片内容项。

    参数:
        slide: 当前幻灯片规格。
        content: 图片描述。
        src: 图片路径。
        alt: 替代文本。

    返回:
        更新后的幻灯片规格。
    """
    return SlideSpec(
        title=slide.title,
        items=slide.items
        + [SlideItem(type=SlideItemType.IMAGE, content=content, meta={"src": src, "alt": alt})],
        layout_hint=slide.layout_hint,
    )


def _parse_table(tokens: list[Token], start_idx: int) -> tuple[str, int, int, int]:
    """解析表格Token。

    参数:
        tokens: Token列表。
        start_idx: 表格开始索引。

    返回:
        (表格内容, 行数, 列数, 结束索引)。
    """
    content = ""
    rows = 0
    cols = 0
    idx = start_idx

    while idx < len(tokens):
        token = tokens[idx]
        if token.type == "table_close":
            break

        if token.type == "tr_open":
            rows += 1

        if token.type == "td_open":
            cols += 1

        if token.type == "inline":
            content += _token_text(token) + "|"

        if token.type == "tr_close":
            content = content.rstrip("|") + "\n"

        idx += 1

    cols = max(cols // rows, 1) if rows > 0 else 1

    return content.strip(), rows, cols, idx


class MarkdownParser:
    """将Markdown文本解析为幻灯片规格的解析器。

    使用markdown-it-py库解析Markdown，通过reduce函数处理Token流，
    将其转换为SlideSpec列表。
    """

    def __init__(self, markdown_text: str) -> None:
        """初始化解析器。

        参数:
            markdown_text: 要解析的Markdown文本。
        """
        self.markdown_text = markdown_text
        self._parser = MarkdownIt("commonmark", {"html": True})
        self._parser.enable(["table", "strikethrough"])

    def parse(self) -> list[SlideSpec]:
        """解析Markdown文本并返回幻灯片规格列表。

        返回:
            解析后的SlideSpec列表。
        """
        tokens = self._parser.parse(self.markdown_text)

        initial_state: tuple[list[SlideSpec], Maybe[SlideSpec], bool, bool, str | None] = (
            [],
            Maybe.from_optional(None),
            False,
            False,
            None,
        )
        slides, current_slide, _, _, _ = reduce(
            self._reducer,
            tokens,
            initial_state,
        )

        slides = current_slide.map(lambda slide: _append_slide(slides, slide)).value_or(slides)

        slides = self._assign_layout_hints(slides)

        return slides

    def _assign_layout_hints(self, slides: list[SlideSpec]) -> list[SlideSpec]:
        """为幻灯片列表分配布局提示。

        如果幻灯片已经有显式的布局提示，则保留；否则根据内容推断。

        参数:
            slides: 幻灯片规格列表。

        返回:
            更新后的幻灯片规格列表，包含布局提示。
        """
        return [
            SlideSpec(
                title=slide.title,
                items=slide.items,
                layout_hint=slide.layout_hint or _infer_layout_hint(slide, idx == 0),
            )
            for idx, slide in enumerate(slides)
        ]

    def _reducer(
        self,
        state: tuple[list[SlideSpec], Maybe[SlideSpec], bool, bool, str | None],
        token: Token,
    ) -> tuple[list[SlideSpec], Maybe[SlideSpec], bool, bool, str | None]:
        """Token流的reduce函数。

        根据不同类型的Token更新解析状态。

        参数:
            state: 当前状态元组 (slides, current_slide, in_list_item, in_table, layout_hint)。
            token: 当前处理的Token。

        返回:
            更新后的状态元组。
        """
        slides, current_slide, in_list_item, in_table, pending_layout_hint = state

        if token.type == "html_inline":
            hint = _parse_layout_hint_from_comment(token.content)
            if hint:
                return slides, current_slide, in_list_item, in_table, hint
            return slides, current_slide, in_list_item, in_table, pending_layout_hint

        if token.type == "html_block":
            hint = _parse_layout_hint_from_comment(token.content)
            if hint:
                return slides, current_slide, in_list_item, in_table, hint
            return slides, current_slide, in_list_item, in_table, pending_layout_hint

        if _is_h1_heading_open(token):
            new_slides = current_slide.map(lambda slide: _append_slide(slides, slide)).value_or(
                slides
            )
            return (
                new_slides,
                Maybe.from_value(SlideSpec(title="", items=[], layout_hint=pending_layout_hint)),
                False,
                False,
                None,
            )

        if _is_inline(token) and not in_list_item and not in_table:
            content = _token_text(token).strip()
            if not content:
                return slides, current_slide, in_list_item, in_table, pending_layout_hint

            runs = _parse_inline_runs(token)

            next_slide = _update_or_create(
                current_slide,
                lambda slide: _add_paragraph_item(slide, content, runs),
                lambda: SlideSpec(title=content, items=[], layout_hint=None),
            )
            return slides, next_slide, False, False, pending_layout_hint

        if _is_list_item_open(token):
            return slides, current_slide, True, False, pending_layout_hint

        if _is_list_item_close(token):
            return slides, current_slide, False, False, pending_layout_hint

        if _is_inline(token) and in_list_item:
            content = _token_text(token).strip()
            if not content:
                return slides, current_slide, in_list_item, False, pending_layout_hint

            runs = _parse_inline_runs(token)

            next_slide = _update_or_create(
                current_slide,
                lambda slide: _add_list_item(slide, content, runs),
                lambda: SlideSpec(
                    title="",
                    items=[
                        SlideItem(type=SlideItemType.LIST, content=content, meta={"runs": runs})
                    ],
                    layout_hint=None,
                ),
            )
            return slides, next_slide, True, False, pending_layout_hint

        if _is_code_block_open(token):
            language = token.info.strip() if token.info else ""
            content = token.content.strip()

            next_slide = _update_or_create(
                current_slide,
                lambda slide: _add_code_block_item(slide, content, language),
                lambda: SlideSpec(
                    title="",
                    items=[
                        SlideItem(
                            type=SlideItemType.CODE, content=content, meta={"language": language}
                        )
                    ],
                    layout_hint=None,
                ),
            )
            return slides, next_slide, False, False, pending_layout_hint

        if _is_table_open(token):
            return slides, current_slide, False, True, pending_layout_hint

        if _is_table_close(token):
            return slides, current_slide, False, False, pending_layout_hint

        if _is_image(token):
            src_raw = token.attrs.get("src", "") if token.attrs else ""
            alt_raw = token.attrs.get("alt", "") if token.attrs else ""
            src = str(src_raw) if src_raw else ""
            alt = str(alt_raw) if alt_raw else ""
            content = alt or src

            next_slide = _update_or_create(
                current_slide,
                lambda slide: _add_image_item(slide, content, src, alt),
                lambda: SlideSpec(
                    title="",
                    items=[
                        SlideItem(
                            type=SlideItemType.IMAGE, content=content, meta={"src": src, "alt": alt}
                        )
                    ],
                    layout_hint=None,
                ),
            )
            return slides, next_slide, False, False, pending_layout_hint

        return slides, current_slide, in_list_item, in_table, pending_layout_hint
