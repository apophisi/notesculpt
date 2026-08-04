# AGENTS.md

## 构建与运行

- **包管理器:** `uv`（非 `pip`）。使用 `uv run`、`uv sync`、`uv add --dev` 等命令。
- **Python 版本:** 3.11（见 `.python-version`）
- **运行主程序:** `uv run python main.py`

## 测试

- **测试命令:** `uv run pytest`（暂无测试文件，这是预期状态）
- 测试框架：`pytest`
- **测试原则:** 遵循 TDD（测试驱动开发），先写失败测试，再实现功能

## 代码质量

- 当前未配置代码检查（lint）、类型检查（typecheck）或格式化工具
- **暂不添加**这些工具，除非项目要求中明确指定

## 项目架构

- 单包项目，入口文件为 `main.py`
- 依赖说明：
  - `click` → CLI 命令行接口
  - `keyring` → 操作系统凭据安全存储
  - `python-dotenv` → 环境变量加载
  - `pytest` → 测试框架

## 工程规范

- 虚拟环境位于 `.venv/`（已加入 .gitignore）
- `.env` 和 `.env.local` 文件已加入 .gitignore — **严禁提交任何密钥/凭证到仓库**
- `opencode.json` 已配置 Superpowers 插件，**请勿移除**

## 语言约束

- **所有对话、提问、建议和生成的文档（SPEC.md、PLAN.md 等）必须使用中文**
- 仅代码本身、CLI 命令、API 名称、标准技术缩写（如 LLM、API、CLI、TDD、CI/CD）可保留英文
- 当不确定时，优先使用中文以确保清晰

## 文档产出要求

- `SPEC.md`、`PLAN.md`、`SPEC_PROCESS.md`、`REFLECTION.md` 均须用中文撰写
- `AGENT_LOG.md` 可用中文记录，技术术语保留英文
- README.md 使用中文撰写，CLI 示例代码块中的命令保留原样

## 当前项目状态

- 项目名称：NoteSculpt（智能笔记精炼器）
- 项目阶段：初始化完成，准备开始 brainstorming
- 核心功能：读取 Markdown 笔记 → 调用 LLM 精炼 → 输出结构清晰的笔记
- 分发方式：Docker 容器 + CI 自动构建