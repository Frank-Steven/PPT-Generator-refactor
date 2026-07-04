"""通用工具函数模块。

集中管理项目中跨模块复用的工具函数，避免代码重复。
"""

from __future__ import annotations

import hashlib
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

from ..core.exceptions import InvalidConfigError

logger = logging.getLogger(__name__)

__all__ = [
    "hex_to_rgb",
    "compute_content_hash",
    "ensure_dir",
    "load_yaml_file",
    "placeholder_type_to_str",
    "safe_run_subprocess",
    "is_windows",
]


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """将十六进制颜色字符串转换为RGB元组。

    参数:
        hex_color: 十六进制颜色字符串，如 "#FF0000" 或 "FF0000"。

    返回:
        (R, G, B) 元组。

    Raises:
        ValueError: 如果颜色格式无效。
    """
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        raise ValueError(f"无效的颜色格式: #{hex_color}")
    return (
        int(hex_color[0:2], 16),
        int(hex_color[2:4], 16),
        int(hex_color[4:6], 16),
    )


def compute_content_hash(content: str, *extra: str) -> str:
    """计算内容的MD5哈希值，用于缓存键。

    参数:
        content: 主要内容。
        *extra: 额外的区分维度（如语言名称）。

    返回:
        16字符的哈希字符串。
    """
    parts = [content, *extra]
    combined = ":".join(parts)
    return hashlib.md5(combined.encode("utf-8")).hexdigest()[:16]


def ensure_dir(path: Path) -> Path:
    """确保目录存在，不存在则创建。

    参数:
        path: 目录路径。

    返回:
        目录路径本身。
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_yaml_file(path: Path, label: str = "YAML文件") -> dict[str, Any]:
    """加载YAML文件并返回字典。

    参数:
        path: YAML文件路径。
        label: 文件标签，用于错误消息（如 "manifest.yaml"）。

    返回:
        解析后的字典。

    Raises:
        FileNotFoundError: 如果文件不存在。
        InvalidConfigError: 如果文件格式无效或内容为空。
    """
    if not path.exists():
        raise FileNotFoundError(f"{label}未找到: {path}")

    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise InvalidConfigError(f"解析{label}失败: {e}") from e

    if data is None:
        raise InvalidConfigError(f"{label}内容为空: {path}")

    if not isinstance(data, dict):
        raise InvalidConfigError(f"{label}格式错误: 期望字典，得到 {type(data).__name__}")

    return data


def placeholder_type_to_str(ph_type: Any) -> str:
    """将python-pptx占位符类型枚举转换为字符串。

    参数:
        ph_type: PP_PLACEHOLDER_TYPE 枚举值。

    返回:
        类型字符串，如 "title"、"body" 等。
    """
    from pptx.enum.shapes import PP_PLACEHOLDER_TYPE

    type_map = {
        PP_PLACEHOLDER_TYPE.TITLE: "title",
        PP_PLACEHOLDER_TYPE.CENTER_TITLE: "center_title",
        PP_PLACEHOLDER_TYPE.SUBTITLE: "subtitle",
        PP_PLACEHOLDER_TYPE.BODY: "body",
        PP_PLACEHOLDER_TYPE.OBJECT: "object",
        PP_PLACEHOLDER_TYPE.PICTURE: "picture",
        PP_PLACEHOLDER_TYPE.FOOTER: "footer",
        PP_PLACEHOLDER_TYPE.DATE: "date",
        PP_PLACEHOLDER_TYPE.SLIDE_NUMBER: "slide_number",
    }
    return type_map.get(ph_type, f"unknown_{ph_type}")


def safe_run_subprocess(
    cmd: list[str],
    timeout: int,
    *,
    shell: bool = False,
    label: str = "命令",
) -> subprocess.CompletedProcess[bytes] | None:
    """安全地运行子进程，统一处理异常。

    参数:
        cmd: 命令及参数列表。
        timeout: 超时秒数。
        shell: 是否使用shell模式。
        label: 命令标签，用于日志。

    返回:
        CompletedProcess如果成功，None如果失败。
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=timeout,
            shell=shell,
        )
        return result
    except subprocess.TimeoutExpired:
        logger.warning(f"{label}超时（{timeout}秒）")
        return None
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        logger.debug(f"{label}执行失败: {exc}")
        return None
    except OSError as exc:
        logger.debug(f"{label}系统错误: {exc}")
        return None


def is_windows() -> bool:
    """判断当前是否为Windows系统。"""
    return sys.platform == "win32"
