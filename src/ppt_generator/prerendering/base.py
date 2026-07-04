"""预渲染器基类。

提供所有预渲染器共享的缓存、哈希和渲染骨架逻辑。
子类只需实现 _render 方法，基类负责缓存管理和错误处理。
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path

from PIL import Image

from ..core.models import PrerenderConfig, PrerenderResult
from ..utils import compute_content_hash, ensure_dir

logger = logging.getLogger(__name__)


class BasePrerenderer(ABC):
    """预渲染器抽象基类。

    模板方法模式：
        prerender() → _compute_hash() → cache check → _render() → save

    子类只需实现:
        - _render(content, output_path) -> tuple[int, int] | None
        - _compute_hash_key(content) -> str  (可选，默认用content本身)
    """

    def __init__(self, config: PrerenderConfig, cache_subdir: str) -> None:
        self._config = config
        self._cache_dir = ensure_dir(config.cache_dir / cache_subdir)

    def prerender(self, content: str, *args: str) -> PrerenderResult | None:
        """预渲染内容的模板方法。

        参数:
            content: 要渲染的内容。
            *args: 额外的区分维度（如语言名称）。

        返回:
            PrerenderResult如果成功，None如果失败。
        """
        content_hash = compute_content_hash(content, *args)
        cache_path = self._cache_dir / f"{content_hash}.png"

        if cache_path.exists():
            return self._load_from_cache(cache_path, content_hash)

        try:
            dimensions = self._render(content, cache_path, *args)
            if dimensions is None:
                return None
            width, height = dimensions
            return PrerenderResult(
                image_path=cache_path,
                width=width,
                height=height,
                content_hash=content_hash,
            )
        except Exception as exc:
            logger.warning(f"{self.__class__.__name__}渲染失败: {exc}", exc_info=True)
            return None

    @abstractmethod
    def _render(self, content: str, output_path: Path, *args: str) -> tuple[int, int] | None:
        """执行实际渲染，返回图片尺寸 (width, height) 或 None。

        参数:
            content: 要渲染的内容。
            output_path: 输出图片路径。
            *args: 额外参数（如语言名称）。

        返回:
            (width, height) 元组如果成功，None如果失败。
        """
        ...

    def _load_from_cache(self, cache_path: Path, content_hash: str) -> PrerenderResult:
        """从缓存加载预渲染结果。"""
        with Image.open(str(cache_path)) as image:
            return PrerenderResult(
                image_path=cache_path,
                width=image.width,
                height=image.height,
                content_hash=content_hash,
            )
