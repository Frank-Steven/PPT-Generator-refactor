<!-- layout: Title Slide -->
# Python函数式编程入门

从基础到实战

<!-- layout: Title and Content -->
# 函数式编程基础

**函数式编程**是一种编程范式，强调使用纯函数和不可变数据。

核心概念：
* **纯函数**：输入相同则输出相同，无副作用
* **不可变数据**：数据创建后不可修改
* **函数组合**：将多个函数组合成新函数
* **声明式编程**：描述"做什么"而非"怎么做"

<!-- layout: Two Content -->
# 核心概念详解

## Lambda表达式

```python
# 匿名函数
add = lambda x, y: x + y
result = add(3, 5)  # 8
```

## Map/Filter/Reduce

```python
numbers = [1, 2, 3, 4, 5]

# Map: 转换每个元素
squares = list(map(lambda x: x ** 2, numbers))  # [1, 4, 9, 16, 25]

# Filter: 筛选元素
evens = list(filter(lambda x: x % 2 == 0, numbers))  # [2, 4]

# Reduce: 累积计算
from functools import reduce
total = reduce(lambda a, b: a + b, numbers)  # 15
```

<!-- layout: Content with Caption -->
# 列表推导

列表推导是Python中函数式编程的利器：

```python
# 基础语法
squares = [x ** 2 for x in range(10)]

# 带条件的列表推导
even_squares = [x ** 2 for x in range(10) if x % 2 == 0]

# 嵌套列表推导
matrix = [[1, 2], [3, 4]]
flattened = [x for row in matrix for x in row]
```

<!-- layout: Title and Content -->
# 生成器与惰性计算

```python
# 生成器表达式
gen = (x ** 2 for x in range(1000000))

# 生成器函数
def fibonacci():
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b

# 使用生成器
for num in fibonacci():
    if num > 100:
        break
    print(num)
```

<!-- layout: Title and Content -->
# 优势与适用场景

**优势：**
* 代码更简洁
* 易于测试和调试
* 天然支持并行处理
* 适合数据处理和管道操作

**适用场景：**
* 数据转换和处理
* 事件驱动编程
* 并发编程
* 管道处理

<!-- layout: Title Slide -->
# 总结

函数式编程为Python带来了新的编程视角。

* **学习曲线平缓**：与Python无缝融合
* **与面向对象互补**：可混合使用
* **在数据分析领域广泛应用**：pandas、PySpark等

**推荐资源：**
* `functools` 模块文档
* `itertools` 模块文档
* `returns` 库：函数式编程工具库