import pytest
from pathlib import Path
import tempfile
import os
from unittest.mock import MagicMock


@pytest.fixture
def temp_dir():
    """创建临时目录，测试结束后自动清理。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_markdown():
    """返回一段示例 Markdown 笔记文本。"""
    return """# 学习笔记：Python 装饰器

## 什么是装饰器
装饰器是 Python 中的一个语法糖，用于修改函数的行为。
装饰器本质上是一个函数，它接受一个函数作为参数，并返回一个新的函数。

## 为什么使用装饰器
使用装饰器可以实现代码复用，避免重复编写相同的逻辑。
比如，我们可以在多个函数上应用相同的日志记录、性能计时、权限检查等逻辑。

## 装饰器的基本语法
```python
@decorator
def my_function():
    pass
```

## 常见装饰器示例
### @staticmethod
将方法转换为静态方法，不需要 self 参数。

### @classmethod
将方法转换为类方法，第一个参数是 cls。

### @property
将方法转换为属性，可以像访问属性一样调用方法。

## 带参数的装饰器
装饰器本身也可以接受参数，这需要额外的一层函数包装。

## 总结
装饰器是 Python 中非常强大的特性，掌握它可以让代码更加简洁和优雅。
"""


@pytest.fixture
def mock_openai_client():
    """创建 mock OpenAI 客户端。"""
    mock = MagicMock()
    mock.chat = MagicMock()
    mock.chat.completions = MagicMock()
    mock.chat.completions.create = MagicMock()
    return mock