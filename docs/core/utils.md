# 工具函数开发文档

## 1. 概述

本模块提供PPT生成器的通用工具函数，集中管理项目中跨模块复用的工具函数，避免代码重复。模块包含颜色转换、哈希计算、目录操作、YAML配置加载、占位符类型转换、子进程执行和平台检测等功能。

所有函数从 `src/ppt_generator/utils/__init__.py` 统一导出，可通过 `from ppt_generator.utils import xxx` 直接导入使用。

## 2. 函数分类

| 分类 | 函数列表 |
|------|----------|
| 路径与文件 | `ensure_dir`、`load_yaml_file` |
| 颜色与哈希 | `hex_to_rgb`、`compute_content_hash` |
| 系统与平台 | `safe_run_subprocess`、`is_windows` |
| 占位符工具 | `placeholder_type_to_str` |

## 3. 函数详细说明

### 3.1 路径与文件

#### 3.1.1 ensure_dir

**定义位置**: [\_\_init\_\_.py#L69-L79](file:///C:/Users/frank/Documents/PPT-Generator/src/ppt_generator/utils/__init__.py#L69-L79)

**函数签名**:
```python
def ensure_dir(path: Path) -> Path
```

确保目录存在，不存在则创建。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| path | Path | 是 | 目录路径 |

| 返回值 | 类型 | 说明 |
|--------|------|------|
| 目录路径 | Path | 目录路径本身 |

**功能描述**:
递归创建指定目录及其所有父目录。如果目录已存在，则不执行任何操作。函数内部使用 `Path.mkdir(parents=True, exist_ok=True)` 实现。

**使用示例**:
```python
from pathlib import Path
from ppt_generator.utils import ensure_dir

output_dir = Path("./output/slides")
ensure_dir(output_dir)
```

---

#### 3.1.2 load_yaml_file

**定义位置**: [\_\_init\_\_.py#L82-L111](file:///C:/Users/frank/Documents/PPT-Generator/src/ppt_generator/utils/__init__.py#L82-L111)

**函数签名**:
```python
def load_yaml_file(path: Path, label: str = "YAML文件") -> dict[str, Any]
```

加载YAML文件并返回字典。

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| path | Path | 是 | - | YAML文件路径 |
| label | str | 否 | "YAML文件" | 文件标签，用于错误消息 |

| 返回值 | 类型 | 说明 |
|--------|------|------|
| 解析结果 | dict[str, Any] | 解析后的字典 |

**抛出异常**:
- `FileNotFoundError`: 如果文件不存在
- `InvalidConfigError`: 如果文件格式无效或内容为空

**功能描述**:
安全加载YAML配置文件，执行多重验证：
1. 检查文件是否存在
2. 使用 `yaml.safe_load` 解析文件内容
3. 验证内容不为空（None）
4. 验证内容类型为字典

**使用示例**:
```python
from pathlib import Path
from ppt_generator.utils import load_yaml_file

config_path = Path("./config.yaml")
config = load_yaml_file(config_path, label="配置文件")
```

---

### 3.2 颜色与哈希

#### 3.2.1 hex_to_rgb

**定义位置**: [\_\_init\_\_.py#L32-L51](file:///C:/Users/frank/Documents/PPT-Generator/src/ppt_generator/utils/__init__.py#L32-L51)

**函数签名**:
```python
def hex_to_rgb(hex_color: str) -> tuple[int, int, int]
```

将十六进制颜色字符串转换为RGB元组。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| hex_color | str | 是 | 十六进制颜色字符串，如 "#FF0000" 或 "FF0000" |

| 返回值 | 类型 | 说明 |
|--------|------|------|
| RGB元组 | tuple[int, int, int] | (R, G, B) 元组 |

**抛出异常**:
- `ValueError`: 如果颜色格式无效

**功能描述**:
将十六进制颜色表示转换为RGB整数元组。支持带 `#` 前缀和不带前缀两种格式。颜色字符串去除 `#` 前缀后必须为6位十六进制字符。

**使用示例**:
```python
from ppt_generator.utils import hex_to_rgb

rgb = hex_to_rgb("#FF0000")  # 返回 (255, 0, 0)
rgb = hex_to_rgb("00FF00")  # 返回 (0, 255, 0)
```

---

#### 3.2.2 compute_content_hash

**定义位置**: [\_\_init\_\_.py#L54-L66](file:///C:/Users/frank/Documents/PPT-Generator/src/ppt_generator/utils/__init__.py#L54-L66)

**函数签名**:
```python
def compute_content_hash(content: str, *extra: str) -> str
```

计算内容的MD5哈希值，用于缓存键。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| content | str | 是 | 主要内容 |
| *extra | str | 否 | 额外的区分维度（如语言名称） |

| 返回值 | 类型 | 说明 |
|--------|------|------|
| 哈希字符串 | str | 16字符的哈希字符串 |

**功能描述**:
计算内容的MD5哈希值，取前16位字符作为结果。支持传入多个额外参数，所有参数用冒号 `:` 连接后统一计算哈希，用于生成缓存键或唯一标识。

**使用示例**:
```python
from ppt_generator.utils import compute_content_hash

content = "幻灯片内容文本"
hash_key = compute_content_hash(content)  # 仅主内容

hash_key = compute_content_hash(content, "zh-CN")  # 主内容 + 语言
```

---

### 3.3 系统与平台

#### 3.3.1 safe_run_subprocess

**定义位置**: [\_\_init\_\_.py#L139-L173](file:///C:/Users/frank/Documents/PPT-Generator/src/ppt_generator/utils/__init__.py#L139-L173)

**函数签名**:
```python
def safe_run_subprocess(
    cmd: list[str],
    timeout: int,
    *,
    shell: bool = False,
    label: str = "命令",
) -> subprocess.CompletedProcess[bytes] | None
```

安全地运行子进程，统一处理异常。

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| cmd | list[str] | 是 | - | 命令及参数列表 |
| timeout | int | 是 | - | 超时秒数 |
| shell | bool | 否 | False | 是否使用shell模式 |
| label | str | 否 | "命令" | 命令标签，用于日志 |

| 返回值 | 类型 | 说明 |
|--------|------|------|
| 执行结果 | subprocess.CompletedProcess[bytes] \| None | 成功返回CompletedProcess，失败返回None |

**功能描述**:
封装 `subprocess.run` 的安全包装函数，统一捕获并记录以下异常：
- `subprocess.TimeoutExpired`: 超时，记录 WARNING 级别日志
- `subprocess.CalledProcessError`、`FileNotFoundError`: 调用错误，记录 DEBUG 级别日志
- `OSError`: 系统错误，记录 DEBUG 级别日志

所有异常均返回 `None`，调用方只需判断返回值是否为 `None` 即可知晓执行是否成功。

**使用示例**:
```python
from ppt_generator.utils import safe_run_subprocess

result = safe_run_subprocess(
    ["python", "--version"],
    timeout=10,
    label="Python版本检查"
)

if result is not None:
    print(result.stdout.decode())
```

---

#### 3.3.2 is_windows

**定义位置**: [\_\_init\_\_.py#L176-L178](file:///C:/Users/frank/Documents/PPT-Generator/src/ppt_generator/utils/__init__.py#L176-L178)

**函数签名**:
```python
def is_windows() -> bool
```

判断当前是否为Windows系统。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| 无 | - | - | - |

| 返回值 | 类型 | 说明 |
|--------|------|------|
| 判断结果 | bool | Windows系统返回True，否则返回False |

**功能描述**:
通过检查 `sys.platform` 是否为 `"win32"` 来判断当前操作系统是否为Windows。

**使用示例**:
```python
from ppt_generator.utils import is_windows

if is_windows():
    print("当前运行在Windows系统")
else:
    print("当前运行在非Windows系统")
```

---

### 3.4 占位符工具

#### 3.4.1 placeholder_type_to_str

**定义位置**: [\_\_init\_\_.py#L114-L136](file:///C:/Users/frank/Documents/PPT-Generator/src/ppt_generator/utils/__init__.py#L114-L136)

**函数签名**:
```python
def placeholder_type_to_str(ph_type: Any) -> str
```

将python-pptx占位符类型枚举转换为字符串。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ph_type | Any | 是 | PP_PLACEHOLDER_TYPE 枚举值 |

| 返回值 | 类型 | 说明 |
|--------|------|------|
| 类型字符串 | str | 类型字符串，如 "title"、"body" 等 |

**功能描述**:
将 `pptx.enum.shapes.PP_PLACEHOLDER_TYPE` 枚举值映射为可读的字符串表示。

支持的映射关系：

| 枚举值 | 字符串 |
|--------|--------|
| TITLE | "title" |
| CENTER_TITLE | "center_title" |
| SUBTITLE | "subtitle" |
| BODY | "body" |
| OBJECT | "object" |
| PICTURE | "picture" |
| FOOTER | "footer" |
| DATE | "date" |
| SLIDE_NUMBER | "slide_number" |

对于未知类型返回 `f"unknown_{ph_type}"` 格式的字符串。

**使用示例**:
```python
from pptx.enum.shapes import PP_PLACEHOLDER_TYPE
from ppt_generator.utils import placeholder_type_to_str

type_str = placeholder_type_to_str(PP_PLACEHOLDER_TYPE.TITLE)
# 返回 "title"
```

## 4. 设计原则

### 4.1 单一职责

每个函数只做一件事，保持函数粒度适中，避免函数功能过于复杂。

### 4.2 错误处理

对于可能失败的操作，提供清晰的错误处理策略：
- 配置加载类函数：抛出明确类型的异常，包含可读的错误信息
- 子进程执行类函数：捕获异常并记录日志，返回None表示失败

### 4.3 类型注解

所有函数均提供完整的类型注解，提升代码可读性和IDE支持。

### 4.4 文档字符串

每个函数都包含完整的docstring，说明参数、返回值和异常信息。
