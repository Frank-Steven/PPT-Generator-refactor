# 命令行接口文档

## 1. 概述

本模块提供PPT生成器的命令行界面，支持从命令行调用生成器，处理参数解析、日志配置和错误处理。

CLI入口定义在 [cli.py](file:///C:/Users/frank/Documents/PPT-Generator/src/ppt_generator/cli.py) 中，通过 `pyproject.toml` 的 `[project.scripts]` 配置为 `ppt-generator` 命令。

## 2. CLI入口

### 2.1 main 函数

**定义位置**: [cli.py#L99-L163](file:///C:/Users/frank/Documents/PPT-Generator/src/ppt_generator/cli.py#L99-L163)

命令行入口函数，负责协调整个CLI流程。

```python
def main(argv: Sequence[str] | None = None) -> int:
```

**参数**:
- `argv`: 命令行参数序列，默认为 `None`（使用 `sys.argv[1:]`）

**返回值**:
- `int`: 退出码（0表示成功）

**执行流程**:
1. 调用 `parse_args` 解析命令行参数
2. 捕获 `SystemExit` 异常（如 `--help` 触发的退出）
3. 调用 `setup_logging` 配置日志
4. 验证输入文件存在性
5. 读取Markdown文件内容
6. 创建 `PPTGenerator` 实例并调用 `generate()`
7. 根据异常类型返回对应退出码

### 2.2 模块直接执行

**定义位置**: [cli.py#L166-L167](file:///C:/Users/frank/Documents/PPT-Generator/src/ppt_generator/cli.py#L166-L167)

```python
if __name__ == "__main__":
    raise SystemExit(main())
```

支持通过 `python -m ppt_generator.cli` 直接执行。

### 2.3 入口点配置

在 `pyproject.toml` 中配置：

```toml
[project.scripts]
ppt-generator = "ppt_generator.cli:main"
```

安装后可通过 `ppt-generator` 命令直接调用。

## 3. 子命令

当前版本采用位置参数模式，暂未实现子命令架构。核心功能通过位置参数直接调用生成流程。

未来可扩展的子命令方向：
- `generate`: 生成PPT（当前默认行为）
- `validate`: 仅验证Markdown格式
- `info`: 查看模板布局信息

## 4. 参数解析

### 4.1 parse_args 函数

**定义位置**: [cli.py#L51-L96](file:///C:/Users/frank/Documents/PPT-Generator/src/ppt_generator/cli.py#L51-L96)

使用 `argparse` 解析命令行参数。

```python
def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
```

### 4.2 参数列表

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `input` | 位置参数 | 是 | - | Markdown源文件路径 |
| `template` | 位置参数 | 是 | - | PPT母版/模板文件路径 |
| `output` | 位置参数 | 是 | - | 输出PowerPoint文件路径 |
| `--title` | 可选参数 | 否 | `"Generated Presentation"` | 演示文稿标题 |
| `-v`, `--verbose` | 标志 | 否 | `False` | 启用详细日志记录 |
| `-h`, `--help` | 标志 | 否 | - | 显示帮助信息 |

### 4.3 解析器配置

**定义位置**: [cli.py#L69-L72](file:///C:/Users/frank/Documents/PPT-Generator/src/ppt_generator/cli.py#L69-L72)

```python
parser = argparse.ArgumentParser(
    prog="ppt-generator",
    description="从结构化Markdown和PPT母版模板创建PowerPoint演示文稿。",
)
```

## 5. 日志配置

### 5.1 setup_logging 函数

**定义位置**: [cli.py#L36-L48](file:///C:/Users/frank/Documents/PPT-Generator/src/ppt_generator/cli.py#L36-L48)

配置全局日志记录。

```python
def setup_logging(verbose: bool = False) -> None:
```

**参数**:
- `verbose`: 如果为 `True`，日志级别设为 `DEBUG`；否则为 `INFO`

**日志格式**:
```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

**示例输出**:
```
2024-01-01 12:00:00,000 - ppt_generator.cli - INFO - 从 input.md 加载Markdown内容
```

## 6. 退出码说明

| 退出码 | 含义 | 触发条件 | 定义位置 |
|--------|------|----------|----------|
| 0 | 成功 | 生成PPT成功或显示帮助 | [cli.py#L150](file:///C:/Users/frank/Documents/PPT-Generator/src/ppt_generator/cli.py#L150) |
| 2 | PPT生成错误 | 捕获 `PPTGeneratorError` | [cli.py#L152-L155](file:///C:/Users/frank/Documents/PPT-Generator/src/ppt_generator/cli.py#L152-L155) |
| 3 | 文件IO错误 | 捕获 `OSError` 或 `IOError` | [cli.py#L156-L159](file:///C:/Users/frank/Documents/PPT-Generator/src/ppt_generator/cli.py#L156-L159) |
| 4 | 未知错误 | 捕获其他未预期异常 | [cli.py#L160-L163](file:///C:/Users/frank/Documents/PPT-Generator/src/ppt_generator/cli.py#L160-L163) |

## 7. 使用示例

### 7.1 基本用法

```bash
ppt-generator input.md template.pptx output.pptx
```

### 7.2 指定标题

```bash
ppt-generator input.md template.pptx output.pptx --title "我的演示文稿"
```

### 7.3 启用详细日志

```bash
ppt-generator input.md template.pptx output.pptx -v
```

### 7.4 查看帮助

```bash
ppt-generator --help
```

**输出**:
```
usage: ppt-generator [-h] [--title TITLE] [-v] input template output

从结构化Markdown和PPT母版模板创建PowerPoint演示文稿。

positional arguments:
  input           Markdown源文件的路径。
  template        PPT母版/模板文件的路径。
  output          输出PowerPoint文件的路径。

options:
  -h, --help      show this help message and exit
  --title TITLE   生成文件的演示文稿标题。
  -v, --verbose   启用详细日志记录。
```

### 7.5 模块方式调用

```bash
python -m ppt_generator.cli input.md template.pptx output.pptx
```

## 8. 错误处理流程

### 8.1 整体流程

```mermaid
flowchart TD
    A[命令行调用] --> B[parse_args解析参数]
    B -->|SystemExit| C[返回退出码]
    B --> D[setup_logging配置日志]
    D --> E[验证文件存在]
    E -->|文件不存在| F[抛出MissingFileError]
    F --> G[捕获PPTGeneratorError]
    G --> H[返回退出码2]
    E --> I[读取Markdown文件]
    I -->|IO失败| J[捕获OSError/IOError]
    J --> K[返回退出码3]
    I --> L[创建PPTGenerator]
    L --> M[调用generate()]
    M -->|成功| N[打印成功信息]
    N --> O[返回退出码0]
    M -->|生成失败| P[捕获PPTGeneratorError]
    P --> Q[返回退出码2]
    M -->|其他异常| R[捕获Exception]
    R --> S[返回退出码4]
```

### 8.2 异常处理层次

**定义位置**: [cli.py#L126-L163](file:///C:/Users/frank/Documents/PPT-Generator/src/ppt_generator/cli.py#L126-L163)

```python
try:
    # ... 主逻辑
except PPTGeneratorError as e:
    logger.error(f"PPT生成错误: {e}")
    print(f"错误: {e}", file=sys.stderr)
    return 2
except (OSError, IOError) as e:
    logger.error(f"文件错误: {e}")
    print(f"文件错误: {e}", file=sys.stderr)
    return 3
except Exception as e:
    logger.exception(f"意外错误: {e}")
    print(f"意外错误: {e}", file=sys.stderr)
    return 4
```

**处理原则**:
1. **特定异常优先**: 先捕获 `PPTGeneratorError`，再捕获IO异常，最后捕获通用异常
2. **双重输出**: 错误信息同时输出到日志和 stderr
3. **完整堆栈**: 未预期异常使用 `logger.exception` 记录完整堆栈跟踪
4. **明确退出码**: 不同错误类型对应不同退出码，便于脚本调用

### 8.3 文件验证

**定义位置**: [cli.py#L127-L136](file:///C:/Users/frank/Documents/PPT-Generator/src/ppt_generator/cli.py#L127-L136)

```python
markdown_path = Path(args.input)
template_path = Path(args.template)
output_path = Path(args.output)

if not markdown_path.exists():
    raise MissingFileError(f"输入文件不存在: {markdown_path}")
if not template_path.exists():
    raise MissingFileError(f"模板文件不存在: {template_path}")

output_path.parent.mkdir(parents=True, exist_ok=True)
```

**验证内容**:
- 输入Markdown文件必须存在
- 模板PPT文件必须存在
- 输出目录自动创建（递归）
