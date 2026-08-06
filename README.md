# NoteSculpt - 智能笔记精炼器

将杂乱的 Markdown 学习笔记，通过 DeepSeek LLM 精炼为结构清晰、重点突出的精炼笔记。

## 获取

### 从源码构建（Docker）

```bash
git clone https://github.com/<your-org>/notesculpt.git
cd notesculpt
docker build -t notesculpt .
```

### 从源码运行（本地 Python）

```bash
git clone https://github.com/<your-org>/notesculpt.git
cd notesculpt
uv sync
```

## 运行

### Docker

```bash
# 查看帮助
docker run notesculpt --help

# 精炼单个文件
docker run -v $(pwd):/data -e DEEPSEEK_API_KEY=sk-xxx notesculpt refine /data/notes.md

# 批量精炼目录
docker run -v $(pwd):/data -e DEEPSEEK_API_KEY=sk-xxx notesculpt refine /data/notes/
```

### 本地

```bash
# 查看帮助
uv run python main.py --help

# 精炼单个文件
uv run python main.py refine my-notes.md

# 批量精炼目录
uv run python main.py refine notes/
```

## API Key 安全配置

NoteSculpt 支持三级优先级链：

| 优先级 | 方式 | 适用场景 |
|--------|------|---------|
| 1（最高） | keyring | 本地桌面使用 |
| 2 | 环境变量 `DEEPSEEK_API_KEY` | Docker / CI/CD |
| 3 | `.env` 文件 | 本地开发 |

### 方式一：keyring（本地桌面）

```bash
notesculpt config set-key
# 输入 API Key（不会回显在终端）
notesculpt config show-status  # 查看状态（不泄露 key）
```

### 方式二：环境变量（Docker / CI）

```bash
export DEEPSEEK_API_KEY=sk-xxxxxxxx
```

### 方式三：.env 文件

```bash
echo "DEEPSEEK_API_KEY=sk-xxxxxxxx" > .env
```

> ⚠️ `.env` 文件已加入 `.gitignore`，**严禁提交到仓库**。

## 精炼控制

```bash
notesculpt refine <目标> [选项]
```

| 选项 | 说明 |
|------|------|
| `--level brief\|moderate\|detailed` | 精炼程度（默认 moderate） |
| `--prompt-file PATH` | 自定义精炼指令文件 |
| `--in-place` | 原地覆盖原文件（需确认） |
| `--stdout` | 输出到终端 |
| `--output-dir PATH` | 指定输出目录 |

## 开发

```bash
uv sync          # 安装依赖
uv run pytest    # 运行测试
```