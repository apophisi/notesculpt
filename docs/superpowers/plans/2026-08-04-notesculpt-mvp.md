# NoteSculpt MVP 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 NoteSculpt 智能笔记精炼器 MVP — 读取杂乱 Markdown 学习笔记，调用 DeepSeek LLM 精炼，输出结构清晰的重点笔记。

**Architecture:** 分层架构，8 个模块按依赖关系自底向上构建：models → errors → config → files → llm → refiner → cli → main。每层严格遵循 TDD（先写失败测试，再实现）。

**Tech Stack:** Python 3.11, uv, click, openai (DeepSeek 兼容), keyring, python-dotenv, pytest

## Global Constraints

- 包管理器：`uv`（非 pip），使用 `uv run`、`uv sync`、`uv add`
- Python 版本：3.11
- 测试框架：pytest，测试命令：`uv run pytest`
- 测试原则：严格 TDD，先写失败测试再实现
- 虚拟环境：`.venv/`（已 gitignored）
- `.env` 和 `.env.local` 已 gitignored，严禁提交密钥
- 包名称：`notesculpt`
- 源代码目录：`notesculpt/`（Python 包），测试目录：`tests/`
- 入口文件：`main.py`（项目根目录）
- 所有文档和注释使用中文

## 文件结构

```
notesculpt/                  ← 新建 Python 包
├── __init__.py              ← 空文件，标记为包
├── models.py                ← 数据模型（dataclass）
├── errors.py                ← 自定义异常层次结构
├── config.py                ← 配置管理（keyring → env → .env）
├── files.py                 ← 文件 I/O 工具函数
├── llm.py                   ← LLM 客户端（OpenAI SDK + 重试）
├── refiner.py               ← 精炼核心逻辑
└── cli.py                   ← Click 命令定义

main.py                      ← 修改：入口点，调用 cli()
tests/                       ← 新建测试目录
├── __init__.py
├── conftest.py              ← 共享 fixtures
├── test_models.py
├── test_errors.py
├── test_config.py
├── test_files.py
├── test_llm.py
├── test_refiner.py
└── test_cli.py

pyproject.toml               ← 修改：添加 openai 依赖 + [project.scripts]
```

---

### Task 1: 项目脚手架搭建

**Files:**
- Create: `notesculpt/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Modify: `pyproject.toml`
- Modify: `main.py`

**Interfaces:**
- Consumes: 无
- Produces: `notesculpt` 包结构，`openai` 依赖，`notesculpt` CLI 入口

- [ ] **Step 1: 创建包目录和空文件**

```bash
mkdir -p notesculpt tests
touch notesculpt/__init__.py tests/__init__.py
```

- [ ] **Step 2: 添加 openai 依赖**

```bash
uv add openai
```

- [ ] **Step 3: 更新 pyproject.toml 添加 CLI 入口**

在 `pyproject.toml` 末尾添加：

```toml
[project.scripts]
notesculpt = "notesculpt.cli:cli"
```

- [ ] **Step 4: 创建 conftest.py 共享 fixtures**

写入 `tests/conftest.py`：

```python
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
```

- [ ] **Step 5: 更新 main.py 为入口点**

将 `main.py` 内容替换为：

```python
from notesculpt.cli import cli


def main():
    cli()


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: 验证脚手架**

```bash
uv run python -c "import notesculpt; print('包导入成功')"
uv run python main.py --help 2>&1 || echo "预期失败：cli 尚未定义，将在 Task 8 实现"
```

- [ ] **Step 7: 提交**

```bash
git add notesculpt/ tests/ main.py pyproject.toml uv.lock
git commit -m "feat: 搭建项目脚手架，添加 openai 依赖和包结构"
```

---

### Task 2: 数据模型（models.py）

**Files:**
- Create: `tests/test_models.py`
- Create: `notesculpt/models.py`

**Interfaces:**
- Consumes: 无
- Produces: `Config`, `RefineRequest`, `RefineResult`, `BatchResult` dataclass

- [ ] **Step 1: 编写测试**

写入 `tests/test_models.py`：

```python
from datetime import datetime
from pathlib import Path
from notesculpt.models import Config, RefineRequest, RefineResult, BatchResult


class TestConfig:
    def test_default_values(self):
        config = Config(api_key="sk-test")
        assert config.api_key == "sk-test"
        assert config.base_url == "https://api.deepseek.com/v1"
        assert config.model == "deepseek-chat"

    def test_custom_values(self):
        config = Config(
            api_key="sk-custom",
            base_url="https://custom.api.com/v1",
            model="custom-model",
        )
        assert config.base_url == "https://custom.api.com/v1"
        assert config.model == "custom-model"


class TestRefineRequest:
    def test_required_fields(self):
        req = RefineRequest(
            content="# Hello",
            file_path=Path("/tmp/test.md"),
            level="moderate",
        )
        assert req.content == "# Hello"
        assert req.file_path == Path("/tmp/test.md")
        assert req.level == "moderate"
        assert req.custom_prompt is None

    def test_with_custom_prompt(self):
        req = RefineRequest(
            content="# Hello",
            file_path=Path("/tmp/test.md"),
            level="brief",
            custom_prompt="请精简为要点",
        )
        assert req.custom_prompt == "请精简为要点"

    def test_level_values(self):
        for level in ("brief", "moderate", "detailed"):
            req = RefineRequest(
                content="test",
                file_path=Path("/tmp/test.md"),
                level=level,
            )
            assert req.level == level


class TestRefineResult:
    def test_all_fields(self):
        now = datetime(2026, 8, 4, 14, 30, 0)
        result = RefineResult(
            original_content="# Original",
            refined_content="# Refined",
            original_chars=10,
            refined_chars=8,
            level="moderate",
            timestamp=now,
        )
        assert result.original_content == "# Original"
        assert result.refined_content == "# Refined"
        assert result.original_chars == 10
        assert result.refined_chars == 8
        assert result.level == "moderate"
        assert result.timestamp == now


class TestBatchResult:
    def test_empty_failures(self):
        result = BatchResult(
            success_count=5,
            failure_count=0,
            failures=[],
            elapsed_seconds=10.5,
        )
        assert result.success_count == 5
        assert result.failure_count == 0
        assert result.failures == []

    def test_with_failures(self):
        failures = [
            (Path("/tmp/a.md"), "权限不足"),
            (Path("/tmp/b.md"), "API 错误"),
        ]
        result = BatchResult(
            success_count=3,
            failure_count=2,
            failures=failures,
            elapsed_seconds=15.0,
        )
        assert result.failure_count == 2
        assert len(result.failures) == 2
        assert result.failures[0][0] == Path("/tmp/a.md")
```

- [ ] **Step 2: 运行测试验证失败**

```bash
uv run pytest tests/test_models.py -v
```

预期：全部 FAIL（模块不存在）

- [ ] **Step 3: 实现 models.py**

写入 `notesculpt/models.py`：

```python
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal


@dataclass
class Config:
    api_key: str
    base_url: str = "https://api.deepseek.com/v1"
    model: str = "deepseek-chat"


@dataclass
class RefineRequest:
    content: str
    file_path: Path
    level: Literal["brief", "moderate", "detailed"]
    custom_prompt: str | None = None


@dataclass
class RefineResult:
    original_content: str
    refined_content: str
    original_chars: int
    refined_chars: int
    level: str
    timestamp: datetime


@dataclass
class BatchResult:
    success_count: int
    failure_count: int
    failures: list[tuple[Path, str]]
    elapsed_seconds: float
```

- [ ] **Step 4: 运行测试验证通过**

```bash
uv run pytest tests/test_models.py -v
```

预期：全部 PASS

- [ ] **Step 5: 提交**

```bash
git add tests/test_models.py notesculpt/models.py
git commit -m "feat: 实现数据模型（Config, RefineRequest, RefineResult, BatchResult）"
```

---

### Task 3: 错误处理（errors.py）

**Files:**
- Create: `tests/test_errors.py`
- Create: `notesculpt/errors.py`

**Interfaces:**
- Consumes: 无
- Produces: `NoteSculptError`, `RetryableError`, `FatalError`, `RateLimitError`, `NetworkError`, `ServerError`, `AuthError`, `ConfigError`, `FileError`

- [ ] **Step 1: 编写测试**

写入 `tests/test_errors.py`：

```python
from notesculpt.errors import (
    NoteSculptError,
    RetryableError,
    FatalError,
    RateLimitError,
    NetworkError,
    ServerError,
    AuthError,
    ConfigError,
    FileError,
)


class TestExceptionHierarchy:
    def test_base_exit_code(self):
        err = NoteSculptError("test")
        assert err.exit_code == 1

    def test_retryable_is_notesculpt_error(self):
        err = RetryableError("retry")
        assert isinstance(err, NoteSculptError)

    def test_fatal_is_notesculpt_error(self):
        err = FatalError("fatal")
        assert isinstance(err, NoteSculptError)

    def test_rate_limit_is_retryable(self):
        err = RateLimitError("rate limited")
        assert isinstance(err, RetryableError)

    def test_network_is_retryable(self):
        err = NetworkError("network down")
        assert isinstance(err, RetryableError)

    def test_server_is_retryable(self):
        err = ServerError("server error")
        assert isinstance(err, RetryableError)

    def test_auth_is_fatal(self):
        err = AuthError("invalid key")
        assert isinstance(err, FatalError)
        assert err.exit_code == 2

    def test_config_is_fatal(self):
        err = ConfigError("missing config")
        assert isinstance(err, FatalError)
        assert err.exit_code == 3

    def test_file_is_fatal(self):
        err = FileError("not found")
        assert isinstance(err, FatalError)
        assert err.exit_code == 4

    def test_error_message(self):
        err = NoteSculptError("something went wrong")
        assert str(err) == "something went wrong"
```

- [ ] **Step 2: 运行测试验证失败**

```bash
uv run pytest tests/test_errors.py -v
```

预期：全部 FAIL

- [ ] **Step 3: 实现 errors.py**

写入 `notesculpt/errors.py`：

```python
class NoteSculptError(Exception):
    exit_code: int = 1

    def __init__(self, message: str):
        super().__init__(message)


class RetryableError(NoteSculptError):
    pass


class RateLimitError(RetryableError):
    pass


class NetworkError(RetryableError):
    pass


class ServerError(RetryableError):
    pass


class FatalError(NoteSculptError):
    pass


class AuthError(FatalError):
    exit_code = 2


class ConfigError(FatalError):
    exit_code = 3


class FileError(FatalError):
    exit_code = 4
```

- [ ] **Step 4: 运行测试验证通过**

```bash
uv run pytest tests/test_errors.py -v
```

预期：全部 PASS

- [ ] **Step 5: 提交**

```bash
git add tests/test_errors.py notesculpt/errors.py
git commit -m "feat: 实现自定义异常层次结构（可恢复/不可恢复错误分类）"
```

---

### Task 4: 配置管理（config.py）

**Files:**
- Create: `tests/test_config.py`
- Create: `notesculpt/config.py`

**Interfaces:**
- Consumes: `Config` (from models.py), `ConfigError` (from errors.py)
- Produces: `ConfigLoader` class (load, set_key, delete_key, get_status)

- [ ] **Step 1: 编写测试**

写入 `tests/test_config.py`：

```python
import os
from unittest.mock import patch, MagicMock
from notesculpt.config import ConfigLoader
from notesculpt.errors import ConfigError


class TestConfigLoaderLoad:
    def test_load_from_keyring(self):
        loader = ConfigLoader()
        with patch("keyring.get_password") as mock_get:
            mock_get.return_value = "sk-keyring-key"
            with patch("os.environ", {}):
                with patch("notesculpt.config.dotenv_values", return_value={}):
                    config = loader.load()
        assert config.api_key == "sk-keyring-key"

    def test_load_falls_back_to_env(self):
        loader = ConfigLoader()
        with patch("keyring.get_password", return_value=None):
            with patch.dict("os.environ", {"DEEPSEEK_API_KEY": "sk-env-key"}, clear=True):
                with patch("notesculpt.config.dotenv_values", return_value={}):
                    config = loader.load()
        assert config.api_key == "sk-env-key"

    def test_load_falls_back_to_dotenv(self):
        loader = ConfigLoader()
        with patch("keyring.get_password", return_value=None):
            with patch.dict("os.environ", {}, clear=True):
                with patch("notesculpt.config.dotenv_values", return_value={"DEEPSEEK_API_KEY": "sk-dotenv-key"}):
                    config = loader.load()
        assert config.api_key == "sk-dotenv-key"

    def test_load_raises_when_no_key(self):
        loader = ConfigLoader()
        with patch("keyring.get_password", return_value=None):
            with patch.dict("os.environ", {}, clear=True):
                with patch("notesculpt.config.dotenv_values", return_value={}):
                    try:
                        loader.load()
                        assert False, "应该抛出 ConfigError"
                    except ConfigError as e:
                        assert "API Key" in str(e)

    def test_load_resolves_base_url(self):
        loader = ConfigLoader()
        with patch("keyring.get_password") as mock_get:
            mock_get.side_effect = lambda s, k: "sk-test" if k == "api_key" else None
            with patch.dict("os.environ", {"DEEPSEEK_BASE_URL": "https://custom.api.com"}, clear=True):
                with patch("notesculpt.config.dotenv_values", return_value={}):
                    config = loader.load()
        assert config.base_url == "https://custom.api.com"

    def test_load_resolves_model(self):
        loader = ConfigLoader()
        with patch("keyring.get_password") as mock_get:
            mock_get.side_effect = lambda s, k: "sk-test" if k == "api_key" else None
            with patch.dict("os.environ", {"DEEPSEEK_MODEL": "deepseek-reasoner"}, clear=True):
                with patch("notesculpt.config.dotenv_values", return_value={}):
                    config = loader.load()
        assert config.model == "deepseek-reasoner"

    def test_load_uses_defaults(self):
        loader = ConfigLoader()
        with patch("keyring.get_password", return_value="sk-test"):
            with patch.dict("os.environ", {}, clear=True):
                with patch("notesculpt.config.dotenv_values", return_value={}):
                    config = loader.load()
        assert config.base_url == "https://api.deepseek.com/v1"
        assert config.model == "deepseek-chat"


class TestConfigLoaderKeyManagement:
    def test_set_key(self):
        loader = ConfigLoader()
        with patch("keyring.set_password") as mock_set:
            loader.set_key("sk-new-key")
        mock_set.assert_called_once_with("notesculpt", "api_key", "sk-new-key")

    def test_delete_key(self):
        loader = ConfigLoader()
        with patch("keyring.delete_password") as mock_delete:
            loader.delete_key()
        mock_delete.assert_called_once_with("notesculpt", "api_key")


class TestConfigLoaderGetStatus:
    def test_status_key_configured(self):
        loader = ConfigLoader()
        with patch("keyring.get_password", return_value="sk-test"):
            with patch.dict("os.environ", {}, clear=True):
                with patch("notesculpt.config.dotenv_values", return_value={}):
                    status = loader.get_status()
        assert status["key_configured"] is True

    def test_status_key_not_configured(self):
        loader = ConfigLoader()
        with patch("keyring.get_password", return_value=None):
            with patch.dict("os.environ", {}, clear=True):
                with patch("notesculpt.config.dotenv_values", return_value={}):
                    status = loader.get_status()
        assert status["key_configured"] is False

    def test_status_shows_model_and_url(self):
        loader = ConfigLoader()
        with patch("keyring.get_password") as mock_get:
            mock_get.side_effect = lambda s, k: "sk-test" if k == "api_key" else None
            with patch.dict("os.environ", {"DEEPSEEK_MODEL": "deepseek-reasoner"}, clear=True):
                with patch("notesculpt.config.dotenv_values", return_value={}):
                    status = loader.get_status()
        assert status["model"] == "deepseek-reasoner"
        assert status["base_url"] == "https://api.deepseek.com/v1"

    def test_status_does_not_leak_key(self):
        loader = ConfigLoader()
        with patch("keyring.get_password", return_value="sk-secret-123"):
            with patch.dict("os.environ", {}, clear=True):
                with patch("notesculpt.config.dotenv_values", return_value={}):
                    status = loader.get_status()
        assert "sk-secret-123" not in str(status)
        assert "api_key" not in status  # 不应包含 key 的实际值字段
```

- [ ] **Step 2: 运行测试验证失败**

```bash
uv run pytest tests/test_config.py -v
```

预期：全部 FAIL

- [ ] **Step 3: 实现 config.py**

写入 `notesculpt/config.py`：

```python
import os
import keyring
from dotenv import dotenv_values
from notesculpt.models import Config
from notesculpt.errors import ConfigError


class ConfigLoader:
    KEYRING_SERVICE = "notesculpt"
    KEYRING_KEY = "api_key"

    def __init__(self):
        self._dotenv = None

    def load(self) -> Config:
        api_key = self._resolve("DEEPSEEK_API_KEY")
        if not api_key:
            raise ConfigError("未找到 API Key。请运行: notesculpt config set-key")
        base_url = self._resolve("DEEPSEEK_BASE_URL") or "https://api.deepseek.com/v1"
        model = self._resolve("DEEPSEEK_MODEL") or "deepseek-chat"
        return Config(api_key=api_key, base_url=base_url, model=model)

    def _resolve(self, key: str) -> str | None:
        value = keyring.get_password(self.KEYRING_SERVICE, key.lower())
        if value:
            return value
        value = os.environ.get(key)
        if value:
            return value
        if self._dotenv is None:
            self._dotenv = dotenv_values(".env")
        return self._dotenv.get(key)

    def set_key(self, api_key: str) -> None:
        keyring.set_password(self.KEYRING_SERVICE, self.KEYRING_KEY, api_key)

    def delete_key(self) -> None:
        keyring.delete_password(self.KEYRING_SERVICE, self.KEYRING_KEY)

    def get_status(self) -> dict:
        has_key = bool(self._resolve("DEEPSEEK_API_KEY"))
        return {
            "key_configured": has_key,
            "model": self._resolve("DEEPSEEK_MODEL") or "deepseek-chat",
            "base_url": self._resolve("DEEPSEEK_BASE_URL") or "https://api.deepseek.com/v1",
        }
```

- [ ] **Step 4: 运行测试验证通过**

```bash
uv run pytest tests/test_config.py -v
```

预期：全部 PASS

- [ ] **Step 5: 提交**

```bash
git add tests/test_config.py notesculpt/config.py
git commit -m "feat: 实现配置管理（keyring → env → .env 三级优先级链）"
```

---

### Task 5: 文件 I/O（files.py）

**Files:**
- Create: `tests/test_files.py`
- Create: `notesculpt/files.py`

**Interfaces:**
- Consumes: `FileError` (from errors.py)
- Produces: `discover_files(path)`, `read_file(path)`, `output_path(input_path, output_dir)`, `write_file(path, content)`, `load_prompt_file(path)`

- [ ] **Step 1: 编写测试**

写入 `tests/test_files.py`：

```python
import pytest
from pathlib import Path
from notesculpt.files import discover_files, read_file, output_path, write_file, load_prompt_file
from notesculpt.errors import FileError


class TestDiscoverFiles:
    def test_single_md_file(self, temp_dir):
        md_file = temp_dir / "test.md"
        md_file.write_text("# Hello")
        result = discover_files(md_file)
        assert result == [md_file]

    def test_non_md_file_raises(self, temp_dir):
        txt_file = temp_dir / "test.txt"
        txt_file.write_text("hello")
        with pytest.raises(FileError, match="不是 Markdown 文件"):
            discover_files(txt_file)

    def test_directory_recursive(self, temp_dir):
        (temp_dir / "a.md").write_text("a")
        (temp_dir / "b.md").write_text("b")
        subdir = temp_dir / "sub"
        subdir.mkdir()
        (subdir / "c.md").write_text("c")
        (temp_dir / "ignore.txt").write_text("ignore")

        result = discover_files(temp_dir)
        assert len(result) == 3
        assert result == sorted(result)

    def test_empty_directory_raises(self, temp_dir):
        with pytest.raises(FileError, match="没有找到"):
            discover_files(temp_dir)

    def test_nonexistent_path_raises(self):
        with pytest.raises(FileError, match="路径不存在"):
            discover_files(Path("/nonexistent/path"))


class TestReadFile:
    def test_read_existing_file(self, temp_dir):
        md_file = temp_dir / "test.md"
        md_file.write_text("# Hello World", encoding="utf-8")
        content = read_file(md_file)
        assert content == "# Hello World"

    def test_read_nonexistent_raises(self):
        with pytest.raises(FileError, match="无法读取"):
            read_file(Path("/nonexistent.md"))


class TestOutputPath:
    def test_default_suffix(self, temp_dir):
        input_path = temp_dir / "notes.md"
        result = output_path(input_path)
        assert result == temp_dir / "notes_refined.md"
        assert result.suffix == ".md"

    def test_with_output_dir(self, temp_dir):
        input_path = temp_dir / "notes.md"
        out_dir = temp_dir / "output"
        result = output_path(input_path, output_dir=out_dir)
        assert result == out_dir / "notes_refined.md"

    def test_preserves_stem(self, temp_dir):
        input_path = temp_dir / "my.notes.md"
        result = output_path(input_path)
        assert result.stem == "my.notes_refined"


class TestWriteFile:
    def test_write_creates_file(self, temp_dir):
        out_path = temp_dir / "output.md"
        write_file(out_path, "# Content")
        assert out_path.exists()
        assert out_path.read_text(encoding="utf-8") == "# Content"

    def test_write_creates_parent_dirs(self, temp_dir):
        out_path = temp_dir / "deep" / "nested" / "output.md"
        write_file(out_path, "# Deep")
        assert out_path.exists()
        assert out_path.read_text(encoding="utf-8") == "# Deep"


class TestLoadPromptFile:
    def test_load_prompt_file(self, temp_dir):
        prompt_file = temp_dir / "custom_prompt.txt"
        prompt_file.write_text("请帮我整理笔记", encoding="utf-8")
        content = load_prompt_file(prompt_file)
        assert content == "请帮我整理笔记"

    def test_load_nonexistent_raises(self):
        with pytest.raises(FileError):
            load_prompt_file(Path("/nonexistent.txt"))
```

- [ ] **Step 2: 运行测试验证失败**

```bash
uv run pytest tests/test_files.py -v
```

预期：全部 FAIL

- [ ] **Step 3: 实现 files.py**

写入 `notesculpt/files.py`：

```python
from pathlib import Path
from notesculpt.errors import FileError

SUFFIX = "_refined"


def discover_files(path: Path) -> list[Path]:
    if not path.exists():
        raise FileError(f"路径不存在: {path}")
    if path.is_file():
        if path.suffix != ".md":
            raise FileError(f"不是 Markdown 文件: {path}")
        return [path]
    if path.is_dir():
        files = sorted(path.rglob("*.md"))
        if not files:
            raise FileError(f"目录中没有找到 .md 文件: {path}")
        return files
    raise FileError(f"路径不存在: {path}")


def read_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        raise FileError(f"无法读取文件 {path}: {e}")


def output_path(input_path: Path, output_dir: Path | None = None) -> Path:
    base = output_dir or input_path.parent
    return base / f"{input_path.stem}{SUFFIX}.md"


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def load_prompt_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        raise FileError(f"无法读取 prompt 文件 {path}: {e}")
```

- [ ] **Step 4: 运行测试验证通过**

```bash
uv run pytest tests/test_files.py -v
```

预期：全部 PASS

- [ ] **Step 5: 提交**

```bash
git add tests/test_files.py notesculpt/files.py
git commit -m "feat: 实现文件 I/O 工具（扫描、读写、路径生成）"
```

---

### Task 6: LLM 客户端（llm.py）

**Files:**
- Create: `tests/test_llm.py`
- Create: `notesculpt/llm.py`

**Interfaces:**
- Consumes: `Config` (from models.py), `NoteSculptError`, `RateLimitError`, `NetworkError`, `ServerError`, `AuthError`, `FatalError` (from errors.py)
- Produces: `LLMClient` class (refine method)

- [ ] **Step 1: 编写测试**

写入 `tests/test_llm.py`：

```python
import pytest
from unittest.mock import patch, MagicMock
from notesculpt.llm import LLMClient
from notesculpt.models import Config
from notesculpt.errors import (
    AuthError,
    RateLimitError,
    NetworkError,
    ServerError,
    FatalError,
)


@pytest.fixture
def config():
    return Config(api_key="sk-test")


@pytest.fixture
def mock_openai():
    with patch("notesculpt.llm.OpenAI") as mock:
        yield mock


class TestLLMClientRefine:
    def test_refine_returns_content(self, config, mock_openai):
        mock_instance = mock_openai.return_value
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "# Refined content"
        mock_instance.chat.completions.create.return_value = mock_response

        client = LLMClient(config)
        result = client.refine("system prompt", "user content")

        assert result == "# Refined content"
        mock_instance.chat.completions.create.assert_called_once()

    def test_refine_passes_correct_params(self, config, mock_openai):
        mock_instance = mock_openai.return_value
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "result"
        mock_instance.chat.completions.create.return_value = mock_response

        client = LLMClient(config)
        client.refine("system prompt", "user content")

        call_kwargs = mock_instance.chat.completions.create.call_args[1]
        assert call_kwargs["model"] == "deepseek-chat"
        assert call_kwargs["temperature"] == 0.3
        assert call_kwargs["messages"][0]["role"] == "system"
        assert call_kwargs["messages"][0]["content"] == "system prompt"
        assert call_kwargs["messages"][1]["role"] == "user"
        assert call_kwargs["messages"][1]["content"] == "user content"

    def test_refine_raises_when_content_empty(self, config, mock_openai):
        mock_instance = mock_openai.return_value
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = ""
        mock_instance.chat.completions.create.return_value = mock_response

        client = LLMClient(config)
        with pytest.raises(FatalError, match="空结果"):
            client.refine("system prompt", "user content")

    def test_refine_raises_when_content_none(self, config, mock_openai):
        mock_instance = mock_openai.return_value
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None
        mock_instance.chat.completions.create.return_value = mock_response

        client = LLMClient(config)
        with pytest.raises(FatalError, match="空结果"):
            client.refine("system prompt", "user content")


class TestLLMClientRetry:
    def test_retries_on_rate_limit(self, config, mock_openai):
        import openai
        mock_instance = mock_openai.return_value
        mock_instance.chat.completions.create.side_effect = [
            openai.RateLimitError("rate limited", response=MagicMock(), body=None),
            openai.RateLimitError("rate limited", response=MagicMock(), body=None),
            MagicMock(choices=[MagicMock(message=MagicMock(content="ok"))]),
        ]

        client = LLMClient(config)
        with patch("time.sleep") as mock_sleep:
            result = client.refine("system", "user")

        assert result == "ok"
        assert mock_instance.chat.completions.create.call_count == 3
        assert mock_sleep.call_count == 2

    def test_retries_on_network_error(self, config, mock_openai):
        import openai
        mock_instance = mock_openai.return_value
        mock_instance.chat.completions.create.side_effect = [
            openai.APIConnectionError(request=MagicMock()),
            MagicMock(choices=[MagicMock(message=MagicMock(content="ok"))]),
        ]

        client = LLMClient(config)
        with patch("time.sleep"):
            result = client.refine("system", "user")

        assert result == "ok"
        assert mock_instance.chat.completions.create.call_count == 2

    def test_retries_on_server_error(self, config, mock_openai):
        import openai
        mock_instance = mock_openai.return_value
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_instance.chat.completions.create.side_effect = [
            openai.APIStatusError("server error", response=mock_response, body=None),
            MagicMock(choices=[MagicMock(message=MagicMock(content="ok"))]),
        ]

        client = LLMClient(config)
        with patch("time.sleep"):
            result = client.refine("system", "user")

        assert result == "ok"
        assert mock_instance.chat.completions.create.call_count == 2

    def test_raises_immediately_on_auth_error(self, config, mock_openai):
        import openai
        mock_instance = mock_openai.return_value
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_instance.chat.completions.create.side_effect = openai.AuthenticationError(
            "invalid key", response=mock_response, body=None
        )

        client = LLMClient(config)
        with pytest.raises(AuthError):
            client.refine("system", "user")
        assert mock_instance.chat.completions.create.call_count == 1

    def test_raises_after_exhausting_retries(self, config, mock_openai):
        import openai
        mock_instance = mock_openai.return_value
        mock_instance.chat.completions.create.side_effect = openai.RateLimitError(
            "rate limited", response=MagicMock(), body=None
        )

        client = LLMClient(config)
        with patch("time.sleep"):
            with pytest.raises(RateLimitError):
                client.refine("system", "user")
        assert mock_instance.chat.completions.create.call_count == 3

    def test_retry_delays_follow_exponential_backoff(self, config, mock_openai):
        import openai
        mock_instance = mock_openai.return_value
        mock_instance.chat.completions.create.side_effect = [
            openai.RateLimitError("rate limited", response=MagicMock(), body=None),
            openai.RateLimitError("rate limited", response=MagicMock(), body=None),
            MagicMock(choices=[MagicMock(message=MagicMock(content="ok"))]),
        ]

        client = LLMClient(config)
        with patch("time.sleep") as mock_sleep:
            client.refine("system", "user")

        sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
        assert sleep_calls == [1, 2]
```

- [ ] **Step 2: 运行测试验证失败**

```bash
uv run pytest tests/test_llm.py -v
```

预期：全部 FAIL

- [ ] **Step 3: 实现 llm.py**

写入 `notesculpt/llm.py`：

```python
import time
import openai
from openai import OpenAI
from notesculpt.models import Config
from notesculpt.errors import (
    NoteSculptError,
    RetryableError,
    RateLimitError,
    NetworkError,
    ServerError,
    AuthError,
    FatalError,
)

MAX_RETRIES = 3
RETRY_DELAYS = [1, 2, 4]


class LLMClient:
    def __init__(self, config: Config):
        self._client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
        )
        self._model = config.model

    def refine(self, system_prompt: str, user_content: str) -> str:
        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                response = self._client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content},
                    ],
                    temperature=0.3,
                )
                content = response.choices[0].message.content
                if not content:
                    raise FatalError("LLM 返回空结果")
                return content
            except NoteSculptError:
                raise
            except Exception as e:
                last_error = self._classify_error(e)
                if isinstance(last_error, FatalError):
                    raise last_error
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAYS[attempt])
                    continue
                raise last_error
        raise last_error  # pragma: no cover

    def _classify_error(self, error: Exception) -> NoteSculptError:
        if isinstance(error, openai.AuthenticationError):
            return AuthError(str(error))
        if isinstance(error, openai.RateLimitError):
            return RateLimitError(str(error))
        if isinstance(error, (openai.APIConnectionError, openai.APITimeoutError)):
            return NetworkError(str(error))
        if isinstance(error, openai.APIStatusError):
            if error.status_code and 500 <= error.status_code < 600:
                return ServerError(str(error))
            return FatalError(str(error))
        return NoteSculptError(str(error))
```

- [ ] **Step 4: 运行测试验证通过**

```bash
uv run pytest tests/test_llm.py -v
```

预期：全部 PASS

- [ ] **Step 5: 提交**

```bash
git add tests/test_llm.py notesculpt/llm.py
git commit -m "feat: 实现 LLM 客户端（OpenAI SDK + 重试 + 错误分类）"
```

---

### Task 7: 精炼核心（refiner.py）

**Files:**
- Create: `tests/test_refiner.py`
- Create: `notesculpt/refiner.py`

**Interfaces:**
- Consumes: `LLMClient` (from llm.py), `RefineRequest`, `RefineResult` (from models.py)
- Produces: `Refiner` class (refine method)

- [ ] **Step 1: 编写测试**

写入 `tests/test_refiner.py`：

```python
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock
from notesculpt.refiner import Refiner, LEVEL_PROMPTS, DEFAULT_SYSTEM_PROMPT
from notesculpt.models import RefineRequest, RefineResult


class TestRefinerRefine:
    def test_refine_returns_result(self):
        mock_llm = MagicMock()
        mock_llm.refine.return_value = "## 核心摘要\n精炼后的内容"

        refiner = Refiner(mock_llm)
        request = RefineRequest(
            content="# Original content",
            file_path=Path("/tmp/test.md"),
            level="moderate",
        )
        result = refiner.refine(request)

        assert isinstance(result, RefineResult)
        assert result.original_content == "# Original content"
        assert result.refined_content == "## 核心摘要\n精炼后的内容"
        assert result.original_chars == 18
        assert result.refined_chars == 14
        assert result.level == "moderate"
        assert isinstance(result.timestamp, datetime)

    def test_refine_calls_llm_with_correct_args(self):
        mock_llm = MagicMock()
        mock_llm.refine.return_value = "result"

        refiner = Refiner(mock_llm)
        request = RefineRequest(
            content="user content here",
            file_path=Path("/tmp/test.md"),
            level="moderate",
        )
        refiner.refine(request)

        call_args = mock_llm.refine.call_args
        system_prompt = call_args[0][0]
        user_content = call_args[0][1]

        assert "中度精炼" in system_prompt
        assert user_content == "user content here"


class TestRefinerPromptBuilding:
    def test_brief_level_prompt(self):
        mock_llm = MagicMock()
        mock_llm.refine.return_value = "result"

        refiner = Refiner(mock_llm)
        request = RefineRequest(
            content="content",
            file_path=Path("/tmp/test.md"),
            level="brief",
        )
        refiner.refine(request)

        system_prompt = mock_llm.refine.call_args[0][0]
        assert "极度精简" in system_prompt

    def test_moderate_level_prompt(self):
        mock_llm = MagicMock()
        mock_llm.refine.return_value = "result"

        refiner = Refiner(mock_llm)
        request = RefineRequest(
            content="content",
            file_path=Path("/tmp/test.md"),
            level="moderate",
        )
        refiner.refine(request)

        system_prompt = mock_llm.refine.call_args[0][0]
        assert "中度精炼" in system_prompt

    def test_detailed_level_prompt(self):
        mock_llm = MagicMock()
        mock_llm.refine.return_value = "result"

        refiner = Refiner(mock_llm)
        request = RefineRequest(
            content="content",
            file_path=Path("/tmp/test.md"),
            level="detailed",
        )
        refiner.refine(request)

        system_prompt = mock_llm.refine.call_args[0][0]
        assert "轻度整理" in system_prompt

    def test_custom_prompt_overrides_default(self):
        mock_llm = MagicMock()
        mock_llm.refine.return_value = "result"

        refiner = Refiner(mock_llm)
        request = RefineRequest(
            content="content",
            file_path=Path("/tmp/test.md"),
            level="moderate",
            custom_prompt="自定义 prompt 指令",
        )
        refiner.refine(request)

        system_prompt = mock_llm.refine.call_args[0][0]
        assert system_prompt == "自定义 prompt 指令"

    def test_default_prompt_contains_output_structure(self):
        mock_llm = MagicMock()
        mock_llm.refine.return_value = "result"

        refiner = Refiner(mock_llm)
        request = RefineRequest(
            content="content",
            file_path=Path("/tmp/test.md"),
            level="moderate",
        )
        refiner.refine(request)

        system_prompt = mock_llm.refine.call_args[0][0]
        assert "核心摘要" in system_prompt
        assert "要点总结" in system_prompt
        assert "关键概念" in system_prompt
        assert "行动项" in system_prompt
        assert "问题与思考" in system_prompt
```

- [ ] **Step 2: 运行测试验证失败**

```bash
uv run pytest tests/test_refiner.py -v
```

预期：全部 FAIL

- [ ] **Step 3: 实现 refiner.py**

写入 `notesculpt/refiner.py`：

```python
from datetime import datetime
from notesculpt.models import RefineRequest, RefineResult

LEVEL_PROMPTS = {
    "brief": "极度精简，每个部分仅保留 1-2 句核心要点。去除所有示例和冗余描述。输出篇幅约为原文的 30-40%。",
    "moderate": "中度精炼，保留主要结构和关键信息，去除重复和明显冗余。输出篇幅约为原文的 50-60%。",
    "detailed": "轻度整理，保留大部分内容，主要做语言润色和结构微调。",
}

DEFAULT_SYSTEM_PROMPT = """你是一个专业的笔记精炼助手。你的任务是将用户提供的杂乱学习笔记整理为结构清晰、重点突出的精炼笔记。

## 精炼要求
{level_instruction}

## 输出格式
请严格按以下结构输出：

### 核心摘要
[2-3 句话概括全文核心观点]

### 要点总结
- 要点 1：...
- 要点 2：...
- 要点 3：...

### [根据内容自适应生成的章节]
根据笔记内容，你可能需要添加以下一个或多个章节：
- 关键概念（如果笔记涉及专业术语）
- 行动项（如果笔记涉及待办事项）
- 问题与思考（如果笔记提出开放性问题）
- 补充说明（如果有需要展开的细节）

## 注意事项
- 保持 Markdown 格式，包括标题层级、列表、代码块等
- 不要添加原文没有的内容
- 不要评价笔记质量，只做精炼整理
"""


class Refiner:
    def __init__(self, llm):
        self._llm = llm

    def refine(self, request: RefineRequest) -> RefineResult:
        system_prompt = self._build_system_prompt(request)
        refined_content = self._llm.refine(system_prompt, request.content)
        return RefineResult(
            original_content=request.content,
            refined_content=refined_content,
            original_chars=len(request.content),
            refined_chars=len(refined_content),
            level=request.level,
            timestamp=datetime.now(),
        )

    def _build_system_prompt(self, request: RefineRequest) -> str:
        if request.custom_prompt:
            return request.custom_prompt
        level_instruction = LEVEL_PROMPTS.get(request.level, LEVEL_PROMPTS["moderate"])
        return DEFAULT_SYSTEM_PROMPT.format(level_instruction=level_instruction)
```

- [ ] **Step 4: 运行测试验证通过**

```bash
uv run pytest tests/test_refiner.py -v
```

预期：全部 PASS

- [ ] **Step 5: 提交**

```bash
git add tests/test_refiner.py notesculpt/refiner.py
git commit -m "feat: 实现精炼核心（prompt 构建 + LLM 调用编排）"
```

---

### Task 8: CLI 命令与入口点（cli.py + main.py 完成）

**Files:**
- Create: `tests/test_cli.py`
- Create: `notesculpt/cli.py`
- Modify: `notesculpt/__init__.py`（如果需要）
- Verify: `main.py`（已在 Task 1 更新）

**Interfaces:**
- Consumes: `ConfigLoader` (config.py), `LLMClient` (llm.py), `Refiner` (refiner.py), `discover_files`, `read_file`, `output_path`, `write_file`, `load_prompt_file` (files.py), `RefineRequest`, `RefineResult`, `BatchResult` (models.py)
- Produces: `cli` Click group, `format_output` 函数

- [ ] **Step 1: 编写测试**

写入 `tests/test_cli.py`：

```python
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from notesculpt.cli import cli, format_output
from notesculpt.models import RefineResult


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def sample_result():
    return RefineResult(
        original_content="原始内容很长" * 100,
        refined_content="## 核心摘要\n\n精炼后的内容",
        original_chars=700,
        refined_chars=18,
        level="moderate",
        timestamp=datetime(2026, 8, 4, 14, 30, 0),
    )


class TestConfigCommands:
    def test_show_status(self, runner):
        with patch("notesculpt.cli.ConfigLoader") as mock_loader_class:
            mock_loader = MagicMock()
            mock_loader.get_status.return_value = {
                "key_configured": True,
                "model": "deepseek-chat",
                "base_url": "https://api.deepseek.com/v1",
            }
            mock_loader_class.return_value = mock_loader

            result = runner.invoke(cli, ["config", "show-status"])
            assert result.exit_code == 0
            assert "API Key 已配置" in result.output
            assert "deepseek-chat" in result.output

    def test_set_key_prompts(self, runner):
        with patch("notesculpt.cli.ConfigLoader") as mock_loader_class:
            mock_loader = MagicMock()
            mock_loader_class.return_value = mock_loader

            result = runner.invoke(cli, ["config", "set-key"], input="sk-test-key\n")
            assert result.exit_code == 0
            mock_loader.set_key.assert_called_once_with("sk-test-key")


class TestRefineCommand:
    def test_refine_help(self, runner):
        result = runner.invoke(cli, ["refine", "--help"])
        assert result.exit_code == 0
        assert "--level" in result.output
        assert "--in-place" in result.output
        assert "--stdout" in result.output
        assert "--output-dir" in result.output

    def test_refine_in_place_and_stdout_mutually_exclusive(self, runner):
        result = runner.invoke(
            cli, ["refine", "test.md", "--in-place", "--stdout"]
        )
        assert result.exit_code != 0
        assert "不能同时使用" in result.output

    def test_refine_in_place_and_output_dir_mutually_exclusive(self, runner):
        result = runner.invoke(
            cli, ["refine", "test.md", "--in-place", "--output-dir", "./out"]
        )
        assert result.exit_code != 0
        assert "不能同时使用" in result.output

    def test_refine_invalid_level(self, runner):
        result = runner.invoke(cli, ["refine", "test.md", "--level", "invalid"])
        assert result.exit_code != 0

    def test_refine_single_file(self, runner, temp_dir, sample_result):
        md_file = temp_dir / "test.md"
        md_file.write_text("# Test content")

        with patch("notesculpt.cli.ConfigLoader") as mock_cfg_class:
            mock_cfg = MagicMock()
            mock_cfg.load.return_value = MagicMock()
            mock_cfg_class.return_value = mock_cfg
            with patch("notesculpt.cli.LLMClient"):
                with patch("notesculpt.cli.Refiner") as mock_refiner_class:
                    mock_refiner = MagicMock()
                    mock_refiner.refine.return_value = sample_result
                    mock_refiner_class.return_value = mock_refiner

                    result = runner.invoke(cli, ["refine", str(md_file)])
                    assert result.exit_code == 0
                    assert (temp_dir / "test_refined.md").exists()

    def test_refine_stdout(self, runner, temp_dir, sample_result):
        md_file = temp_dir / "test.md"
        md_file.write_text("# Test content")

        with patch("notesculpt.cli.ConfigLoader") as mock_cfg_class:
            mock_cfg = MagicMock()
            mock_cfg.load.return_value = MagicMock()
            mock_cfg_class.return_value = mock_cfg
            with patch("notesculpt.cli.LLMClient"):
                with patch("notesculpt.cli.Refiner") as mock_refiner_class:
                    mock_refiner = MagicMock()
                    mock_refiner.refine.return_value = sample_result
                    mock_refiner_class.return_value = mock_refiner

                    result = runner.invoke(cli, ["refine", str(md_file), "--stdout"])
                    assert result.exit_code == 0
                    assert "核心摘要" in result.output
                    assert "精炼信息" in result.output

    def test_refine_batch_shows_summary(self, runner, temp_dir, sample_result):
        (temp_dir / "a.md").write_text("# A")
        (temp_dir / "b.md").write_text("# B")

        with patch("notesculpt.cli.ConfigLoader") as mock_cfg_class:
            mock_cfg = MagicMock()
            mock_cfg.load.return_value = MagicMock()
            mock_cfg_class.return_value = mock_cfg
            with patch("notesculpt.cli.LLMClient"):
                with patch("notesculpt.cli.Refiner") as mock_refiner_class:
                    mock_refiner = MagicMock()
                    mock_refiner.refine.return_value = sample_result
                    mock_refiner_class.return_value = mock_refiner

                    result = runner.invoke(cli, ["refine", str(temp_dir)])
                    assert result.exit_code == 0
                    assert "批量处理完成" in result.output
                    assert "成功" in result.output


class TestFormatOutput:
    def test_format_output_includes_metadata(self, sample_result):
        output = format_output(sample_result)
        assert "精炼信息" in output
        assert "2026-08-04 14:30:00" in output
        assert "moderate" in output
        assert "压缩比" in output
        assert "核心摘要" in output

    def test_format_output_calculates_ratio(self, sample_result):
        output = format_output(sample_result)
        assert "97%" in output  # (1 - 18/700) * 100 ≈ 97%

    def test_format_output_includes_refined_content(self, sample_result):
        output = format_output(sample_result)
        assert "精炼后的内容" in output
```

- [ ] **Step 2: 运行测试验证失败**

```bash
uv run pytest tests/test_cli.py -v
```

预期：全部 FAIL

- [ ] **Step 3: 实现 cli.py**

写入 `notesculpt/cli.py`：

```python
import time
import click
from pathlib import Path
from notesculpt.config import ConfigLoader
from notesculpt.llm import LLMClient
from notesculpt.refiner import Refiner
from notesculpt.files import discover_files, read_file, output_path, write_file, load_prompt_file
from notesculpt.models import RefineRequest, RefineResult


@click.group()
def cli():
    """NoteSculpt — 智能笔记精炼器"""


@cli.command()
@click.argument("target", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--level",
    type=click.Choice(["brief", "moderate", "detailed"]),
    default="moderate",
    help="精炼程度",
)
@click.option(
    "--prompt-file",
    type=click.Path(exists=True, path_type=Path),
    help="自定义精炼指令文件",
)
@click.option("--in-place", is_flag=True, help="原地覆盖原文件")
@click.option("--stdout", is_flag=True, help="输出到标准输出")
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    help="指定输出目录",
)
def refine(target, level, prompt_file, in_place, stdout, output_dir):
    """精炼 Markdown 笔记"""
    if in_place and stdout:
        raise click.UsageError("--in-place 和 --stdout 不能同时使用")
    if in_place and output_dir:
        raise click.UsageError("--in-place 和 --output-dir 不能同时使用")

    if in_place:
        click.confirm("⚠ 原地覆盖模式将直接修改原文件，是否继续？", abort=True)

    config = ConfigLoader().load()
    llm = LLMClient(config)
    refiner = Refiner(llm)

    custom_prompt = load_prompt_file(prompt_file) if prompt_file else None
    files = discover_files(target)
    results = []
    failures = []
    start_time = time.time()

    for file_path in files:
        try:
            content = read_file(file_path)
            request = RefineRequest(
                content=content,
                file_path=file_path,
                level=level,
                custom_prompt=custom_prompt,
            )
            result = refiner.refine(request)
            results.append(result)

            output = format_output(result)
            if stdout:
                click.echo(output)
            elif in_place:
                write_file(file_path, output)
            else:
                out = output_path(file_path, output_dir)
                write_file(out, output)
                click.echo(f"✓ {file_path.name} → {out.name}")
        except Exception as e:
            failures.append((file_path, str(e)))
            click.echo(f"✗ {file_path.name}: {e}", err=True)
            if len(files) == 1:
                raise

    if len(files) > 1:
        elapsed = time.time() - start_time
        click.echo()
        click.echo("📊 批量处理完成")
        click.echo("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        click.echo(f"成功：{len(results)}/{len(files)} 个文件")
        click.echo(f"失败：{len(failures)}/{len(files)} 个文件")
        if failures:
            click.echo("失败文件：")
            for path, error in failures:
                click.echo(f"  - {path}：{error}")
        click.echo(f"处理耗时：{elapsed:.1f}s")


@cli.group()
def config():
    """管理 API Key 配置"""


@config.command("set-key")
def set_key():
    """将 API Key 存入系统 keyring"""
    api_key = click.prompt("请输入 DeepSeek API Key", hide_input=True)
    loader = ConfigLoader()
    loader.set_key(api_key)
    click.echo("✓ API Key 已存入 keyring")


@config.command("delete-key")
def delete_key():
    """从 keyring 中删除 API Key"""
    loader = ConfigLoader()
    loader.delete_key()
    click.echo("✓ API Key 已从 keyring 删除")


@config.command("show-status")
def show_status():
    """显示当前配置状态"""
    loader = ConfigLoader()
    status = loader.get_status()
    click.echo(f"API Key 已配置: {'是' if status['key_configured'] else '否'}")
    click.echo(f"模型: {status['model']}")
    click.echo(f"API 地址: {status['base_url']}")


def format_output(result: RefineResult) -> str:
    if result.original_chars > 0:
        ratio = (1 - result.refined_chars / result.original_chars) * 100
    else:
        ratio = 0.0
    return f"""> 📝 **精炼信息**
> - 精炼时间：{result.timestamp:%Y-%m-%d %H:%M:%S}
> - 原始字数：{result.original_chars:,} 字 → 精炼后：{result.refined_chars:,} 字
> - 精炼级别：{result.level}
> - 压缩比：{ratio:.0f}%

{result.refined_content}"""
```

- [ ] **Step 4: 运行测试验证通过**

```bash
uv run pytest tests/test_cli.py -v
```

预期：全部 PASS

- [ ] **Step 5: 验证 CLI 可正常运行**

```bash
uv run python main.py --help
uv run python main.py refine --help
uv run python main.py config --help
```

- [ ] **Step 6: 提交**

```bash
git add tests/test_cli.py notesculpt/cli.py
git commit -m "feat: 实现 CLI 命令（refine + config 子命令组）"
```

---

### Task 9: 集成验证

**Files:**
- 无新建文件

**Interfaces:**
- Consumes: 所有已完成模块
- Produces: 完整的可运行应用

- [ ] **Step 1: 运行全部测试**

```bash
uv run pytest tests/ -v
```

预期：所有测试 PASS

- [ ] **Step 2: 验证 CLI 端到端流程（使用 --help 检查所有命令）**

```bash
uv run python main.py --help
uv run python main.py refine --help
uv run python main.py config --help
uv run python main.py config show-status
```

- [ ] **Step 3: 验证包安装和 CLI 入口**

```bash
uv run pip install -e . 2>/dev/null || true
uv run notesculpt --help
```

- [ ] **Step 4: 提交**

```bash
git add -A
git commit -m "chore: 集成验证通过，MVP 实现完成"
```