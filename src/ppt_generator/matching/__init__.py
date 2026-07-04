"""布局匹配与分页模块。

提供幻灯片布局自动匹配和自动分页功能。
"""

from .layout_matcher import LayoutMatcher, create_matcher_with_rules
from .pagination import PaginationConfig, paginate_slide, paginate_slides


__all__ = [
    "LayoutMatcher",
    "create_matcher_with_rules",
    "PaginationConfig",
    "paginate_slide",
    "paginate_slides",
]