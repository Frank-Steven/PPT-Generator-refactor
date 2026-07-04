"""布局匹配器模块。

本模块负责根据幻灯片规格自动选择最合适的布局。
使用函数式编程风格，通过returns.Maybe monad处理可能的空值。

布局匹配策略:
1. 首先尝试精确匹配布局名称
2. 如果没有精确匹配，则根据布局提示进行模糊匹配
3. 模糊匹配使用layouts.yaml中定义的关键词
4. 最后返回默认布局（由layouts.yaml的defaults定义）
"""

from __future__ import annotations

from collections.abc import Callable

from returns.maybe import Maybe, Nothing

from ..core.models import LayoutConfig, LayoutSpec, SlideSpec


class LayoutMatcher:
    """布局匹配器。

    根据幻灯片规格和LayoutConfig自动选择最合适的布局。
    布局的元数据、关键词和默认值都来自layouts.yaml。
    """

    def __init__(
        self,
        layout_config: LayoutConfig | None = None,
        strategy: Callable[[SlideSpec, list[LayoutSpec], LayoutConfig | None], Maybe[LayoutSpec]]
        | None = None,
    ) -> None:
        """初始化布局匹配器。

        参数:
            layout_config: 布局配置，来自layouts.yaml。None时使用退化策略。
            strategy: 自定义匹配策略函数。
        """
        self._layout_config = layout_config
        self._strategy = strategy or self._default_strategy

    def select_layout(self, slide: SlideSpec, layouts: list[LayoutSpec]) -> Maybe[LayoutSpec]:
        """选择最合适的布局。

        参数:
            slide: 幻灯片规格。
            layouts: 可用布局列表。

        返回:
            Maybe[LayoutSpec]，包含匹配的布局或Nothing。
        """
        return self._strategy(slide, layouts, self._layout_config)

    def _default_strategy(
        self,
        slide: SlideSpec,
        layouts: list[LayoutSpec],
        layout_config: LayoutConfig | None,
    ) -> Maybe[LayoutSpec]:
        """默认布局匹配策略。

        优先级：精确匹配 > 关键词模糊匹配 > 默认布局

        参数:
            slide: 幻灯片规格。
            layouts: 可用布局列表。
            layout_config: 布局配置。

        返回:
            Maybe[LayoutSpec]，包含匹配的布局或Nothing。
        """
        layout_hint = slide.layout_hint

        if layout_hint:
            exact_match = self._find_exact_match(layout_hint, layouts)
            if exact_match is not Nothing:
                return exact_match

            fuzzy_match = self._find_fuzzy_match(layout_hint, layouts, layout_config)
            if fuzzy_match is not Nothing:
                return fuzzy_match

        return self._find_default_layout(layouts, layout_config)

    def _find_exact_match(self, layout_name: str, layouts: list[LayoutSpec]) -> Maybe[LayoutSpec]:
        """查找精确匹配的布局。

        参数:
            layout_name: 布局名称。
            layouts: 可用布局列表。

        返回:
            Maybe[LayoutSpec]，包含匹配的布局或Nothing。
        """
        return Maybe.from_optional(
            next((layout for layout in layouts if layout.name == layout_name), None)
        )

    def _find_fuzzy_match(
        self,
        layout_hint: str,
        layouts: list[LayoutSpec],
        layout_config: LayoutConfig | None,
    ) -> Maybe[LayoutSpec]:
        """根据布局提示查找模糊匹配的布局。

        如果有layout_config，则使用其中定义的关键词进行匹配；
        否则退化为基于布局名称的简单匹配。

        参数:
            layout_hint: 布局提示。
            layouts: 可用布局列表。
            layout_config: 布局配置。

        返回:
            Maybe[LayoutSpec]，包含匹配的布局或Nothing。
        """
        hint_lower = layout_hint.lower()

        if layout_config is not None:
            best_match = max(
                layout_config.layouts,
                key=lambda ld: self._calculate_keyword_score(hint_lower, ld.keywords),
                default=None,
            )

            if (
                best_match is not None
                and self._calculate_keyword_score(hint_lower, best_match.keywords) > 0
            ):
                layout = next(
                    (layout for layout in layouts if layout.name == best_match.name), None
                )
                if layout is not None:
                    return Maybe.from_value(layout)

        return Maybe.from_optional(
            next(
                (
                    layout
                    for keyword in hint_lower.split()
                    for layout in layouts
                    if keyword in layout.name.lower()
                ),
                None,
            )
        )

    def _calculate_keyword_score(self, hint_lower: str, keywords: list[str]) -> int:
        """计算提示与关键词列表的匹配分数。

        参数:
            hint_lower: 小写的布局提示。
            keywords: 关键词列表。

        返回:
            匹配分数（匹配的关键词数量）。
        """
        return sum(1 for kw in keywords if kw.lower() in hint_lower)

    def _find_default_layout(
        self,
        layouts: list[LayoutSpec],
        layout_config: LayoutConfig | None,
    ) -> Maybe[LayoutSpec]:
        """查找默认布局。

        如果有layout_config，使用其中定义的默认布局；
        否则退化为基于名称的启发式查找。

        参数:
            layouts: 可用布局列表。
            layout_config: 布局配置。

        返回:
            Maybe[LayoutSpec]，包含默认布局或Nothing。
        """
        if layout_config is not None:
            default_name = layout_config.get_default_layout_name("default")
            layout = next((layout for layout in layouts if layout.name == default_name), None)
            if layout is not None:
                return Maybe.from_value(layout)

        # 启发式回退：按优先级查找
        predicates: list[Callable[[LayoutSpec], bool]] = [
            lambda layout: "title" in layout.name.lower() and "content" in layout.name.lower(),
            lambda layout: "content" in layout.name.lower(),
        ]

        for predicate in predicates:
            layout = next((layout for layout in layouts if predicate(layout)), None)
            if layout is not None:
                return Maybe.from_value(layout)

        if layouts:
            return Maybe.from_value(layouts[0])

        return Nothing

    def with_strategy(
        self,
        strategy: Callable[[SlideSpec, list[LayoutSpec], LayoutConfig | None], Maybe[LayoutSpec]],
    ) -> LayoutMatcher:
        """返回使用新策略的 LayoutMatcher 实例（不可变更新）。

        参数:
            strategy: 自定义匹配策略函数。

        返回:
            新的 LayoutMatcher 实例。
        """
        return LayoutMatcher(
            layout_config=self._layout_config,
            strategy=strategy,
        )

    @property
    def layout_config(self) -> LayoutConfig | None:
        """获取布局配置。"""
        return self._layout_config


def create_matcher_with_rules(
    custom_rules: list[tuple[str, list[str]]],
    layout_config: LayoutConfig | None = None,
) -> LayoutMatcher:
    """创建带有自定义匹配规则的布局匹配器。

    参数:
        custom_rules: 自定义匹配规则列表，每个规则是(目标布局名称, 关键词列表)。
        layout_config: 可选的布局配置。

    返回:
        LayoutMatcher实例。
    """

    def custom_strategy(
        slide: SlideSpec,
        layouts: list[LayoutSpec],
        lc: LayoutConfig | None,
    ) -> Maybe[LayoutSpec]:
        layout_hint = slide.layout_hint

        if layout_hint:
            hint_lower = layout_hint.lower()

            for target_name, keywords in custom_rules:
                if all(keyword in hint_lower for keyword in keywords):
                    for layout in layouts:
                        if target_name.lower() in layout.name.lower():
                            return Maybe.from_value(layout)

        return LayoutMatcher(layout_config=lc)._default_strategy(slide, layouts, lc)

    return LayoutMatcher(layout_config=layout_config, strategy=custom_strategy)
