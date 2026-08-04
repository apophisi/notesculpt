# NoteSculpt 设计规格

**日期：** 2026-08-04
**状态：** 待评审

---

## 1. 项目概述

NoteSculpt 是一个智能笔记精炼器，读取杂乱 Markdown 学习笔记 → 调用 LLM 精炼 → 输出结构清晰的精炼笔记。当前 MVP 聚焦场景 A：将零散/冗长的学习笔记整理为结构化要点总结。

### 技术栈

- **语言：** Python 3.11
- **包管理：** uv
- **CLI 框架：** click
- **LLM SDK：** openai（base_url 指向 DeepSeek API）
- **凭据存储：** keyring
- **环境变量：** python-dotenv
- **测试：** pytest（TDD）
- **模型：** deepseek-chat（主力），可通过配置切换

---

## 2. 架构设计

采用分层架构（方案 B），共 8 个模块：

```
notesculpt/
├── cli.py          ← Click 命令定义（参数解析、输出格式化）
├── refiner.py      ← 精炼核心逻辑（prompt 构建、LLM 调用、结果处理）
├── llm.py          ← LLM 客户端封装（OpenAI SDK + 重试逻辑）
├── config.py       ← 配置管理（keyring → env → .env 优先级链）
├── files.py        ← 文件遍历与 I/O
├── models.py       ← 数据模型（dataclass）
├── errors.py       ← 自定义异常分类
└── main.py         ← 入口点
```

**依赖关系：** cli → refiner → llm → config, cli → files, 所有模块 → models + errors

---

## 3. 数据模型（models.py）

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

---

## 4. 错误处理（errors.py）

异常层次结构，按可恢复/不可恢复分类：

```
NoteSculptError (base, exit_code=1)
├── RetryableError          ← 触发自动重试
│   ├── RateLimitError      ← HTTP 429
│   ├── NetworkError        ← 网络超时/连接失败
│   └── ServerError         ← HTTP 5xx
└── FatalError              ← 立即失败，不重试
    ├── AuthError           ← HTTP 401, exit_code=2
    ├── ConfigError         ← 配置缺失/无效, exit_code=3
    └── FileError           ← 文件不存在/权限/非 .md, exit_code=4
```

---

## 5. 配置管理（config.py）

**优先级链：** keyring → 环境变量 → `.env` 文件

支持的环境变量：
- `DEEPSEEK_API_KEY`（必需）
- `DEEPSEEK_BASE_URL`（默认 `https://api.deepseek.com/v1`）
- `DEEPSEEK_MODEL`（默认 `deepseek-chat`）

`ConfigLoader` 提供：
- `load()` — 按优先级链解析配置，找不到 API Key 时抛出 `ConfigError`
- `set_key(api_key)` — 存入 keyring
- `delete_key()` — 从 keyring 删除
- `get_status()` — 返回状态（不泄露 key 值）

使用 `dotenv_values()` 而非 `load_dotenv()`，避免污染 `os.environ`。

---

## 6. LLM 客户端（llm.py）

封装 OpenAI SDK，内置重试逻辑：

- **重试策略：** 最多 3 次，指数退避 1s → 2s → 4s
- **重试条件：** 仅 `RetryableError` 子类触发
- **固定参数：** `temperature=0.3`
- **错误映射：** OpenAI SDK 异常 → NoteSculpt 异常类型
  - `openai.AuthenticationError` → `AuthError`
  - `openai.RateLimitError` → `RateLimitError`
  - `openai.APIConnectionError` / `APITimeoutError` → `NetworkError`
  - `openai.APIStatusError` (5xx) → `ServerError`
  - `openai.APIStatusError` (4xx, 非 401/429) → `FatalError`
- **空结果检查：** 响应 content 为空时抛出 `FatalError`

接口：`LLMClient(refine(system_prompt, user_content) -> str)`

---

## 7. 文件 I/O（files.py）

- `discover_files(path)` — 单文件返回 `[path]`，目录递归扫描 `.md`，不存在或无 `.md` 抛 `FileError`
- `read_file(path)` — 读取 UTF-8 文本，失败抛 `FileError`
- `output_path(input_path, output_dir)` — 生成 `{stem}_refined.md` 路径
- `write_file(path, content)` — 写入文件，自动创建父目录

仅支持 `.md` 扩展名（MVP 不处理 `.markdown`）。

---

## 8. 精炼核心（refiner.py）

### 精炼级别

| 级别 | 描述 | 参考篇幅 |
|------|------|---------|
| `brief` | 极度精简，每部分仅 1-2 句核心要点 | ~30-40% |
| `moderate` | 中度精炼，保留主要结构，去冗余 | ~50-60%（默认） |
| `detailed` | 轻度整理，保留大部分内容，语言润色 | ~80%+ |

### 默认 Prompt 结构

- 固定章节：核心摘要 → 要点总结
- 自适应章节：LLM 根据内容生成（关键概念 / 行动项 / 问题与思考 / 补充说明）

### 自定义 Prompt

`--prompt-file` 加载的内容作为 system prompt 完全覆盖默认 prompt，笔记内容始终作为 user message 传入。

### 接口

`Refiner(llm: LLMClient)` → `refine(request: RefineRequest) -> RefineResult`

---

## 9. CLI 命令（cli.py）

### 命令结构

```
notesculpt refine <目标>        # 精炼笔记
notesculpt config set-key       # 设置 API Key
notesculpt config delete-key    # 删除 API Key
notesculpt config show-status   # 查看配置状态
```

### refine 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `target` | PATH（必须） | — | 文件或目录 |
| `--level` | choice | moderate | brief / moderate / detailed |
| `--prompt-file` | PATH | — | 自定义 prompt 文件 |
| `--in-place` | flag | — | 原地覆盖（与 `--stdout`/`--output-dir` 互斥） |
| `--stdout` | flag | — | 输出到终端（与 `--in-place` 互斥） |
| `--output-dir` | PATH | — | 指定输出目录（与 `--in-place` 互斥） |

### 行为规则

- 默认：单文件 → `{stem}_refined.md`；目录 → 递归处理所有 `.md`
- 单文件模式错误直接抛出，批量模式错误汇总后报告
- 输出格式：元信息引用块 + 精炼内容

### 输出格式

```
> 📝 **精炼信息**
> - 精炼时间：YYYY-MM-DD HH:MM:SS
> - 原始字数：N 字 → 精炼后：M 字
> - 精炼级别：moderate
> - 压缩比：X%

[精炼后的 Markdown 内容]
```

---

## 10. 测试策略

遵循 TDD，每个模块对应独立测试文件：

- 数据模型：值对象创建和字段验证
- 错误处理：异常类型和退出码
- 配置管理：优先级链、keyring mock、缺失配置
- LLM 客户端：重试逻辑、错误分类、空结果
- 文件 I/O：路径发现、读写、输出路径生成
- 精炼核心：prompt 构建、自定义 prompt 覆盖
- CLI：参数互斥、输出格式、批量汇总

LLM 客户端和精炼核心测试中使用 mock，不实际调用 API。

---

## 11. 范围边界

### MVP 包含
- 单文件/批量精炼
- 三种精炼级别（brief / moderate / detailed）
- 自定义 prompt 文件
- keyring + env + .env 三级配置
- 自动重试（指数退避）
- 批量容错与汇总报告
- 元信息块输出

### v2 扩展（不在此次范围）
- 语言润色（B）
- 知识图谱关联（C）
- `--temperature` 参数
- `--preserve-topics` 参数
- 交互式精炼
- 失败缓存/断点续传
- `.markdown` 扩展名支持
- YAML front matter 元数据
- `~/.config/notesculpt/config.toml` 配置文件