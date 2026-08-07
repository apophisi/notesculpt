### Task 1: 项目脚手架搭建

- **时间：** 2026-08-05
- **执行方式：** 冷启动验证（独立 agent）
- **产出 commit：** 85eaaf6
- **测试结果：** 包导入成功，CLI 入口预期失败（Task 8 实现）
- **评审结果：** ✅ 通过
- **人工干预：** 无
- **学到的教训：** PLAN 中未明确文件路径，agent 将 models.py 写入项目根目录（已在 SPEC/PLAN 中修正）

### Task 2: 数据模型（models.py）

- **时间：** 2026-08-05
- **执行方式：** 冷启动验证（独立 agent）
- **产出 commit：** 0eb01e1
- **测试结果：** 8/8 通过
- **评审结果：** ✅ 通过
- **人工干预：** 文件路径修正（移入 notesculpt/ 包目录）
- **学到的教训：** TDD 流程严格执行，红→绿→重构

### Task 3: 错误处理（errors.py）

- **时间：** 2026-08-05
- **Subagent：** OpenCode SDD 工作流
- **产出 commit：** 614f836（主实现），后补风格修复
- **测试结果：** 9/9 通过
- **评审结果：** ✅ 通过
- **人工干预：** 文件末尾补充换行符（PEP 8）
- **学到的教训：** Subagent 完成 Task 后会自动推进，需要在 prompt 中明确停止点

### Task 4: 配置管理（config.py）

- **时间：** 2026-08-05
- **Subagent：** OpenCode SDD 工作流
- **产出 commit：** 10631f2
- **测试结果：** 13/13 通过，全量 31/31 通过
- **评审结果：** ✅ 通过
- **人工干预：** 无
- **修正记录：** 测试中 keyring 键名修正（`api_key` → `deepseek_api_key`），匹配 `_resolve()` 的 `key.lower()` 行为
- **学到的教训：** PLAN 中的测试代码与实际实现可能存在细微不一致，Subagent 可自行修正

### Task 5: 文件 I/O（files.py）

- **时间：** 2026-08-05
- **Subagent：** OpenCode SDD 工作流
- **产出 commit：** 6d975ad
- **测试结果：** 14/14 通过，全量 45/45 通过
- **评审结果：** ✅ 通过
- **人工干预：** 无
- **修正记录：** `files.py` 再次被写入项目根目录，Subagent 自行 `mv` 修正（与 Task 2 相同模式）
- **学到的教训：** PLAN.md 中「文件必须在 notesculpt/ 包目录下」的约束需要更显式地强调，或作为全局约束放在 PLAN 开头

### Task 6: LLM 客户端（llm.py）

- **时间：** 2026-08-05
- **Subagent：** OpenCode SDD 工作流
- **产出 commit：** 6f501ba
- **测试结果：** 10/10 通过，全量 55/55 通过
- **评审结果：** ✅ 通过
- **人工干预：** 无
- **修正记录：** 无
- **学到的教训：** LLM 客户端重试逻辑测试需要 mock OpenAI SDK 异常类型，`openai.RateLimitError` 等需传入 `response` 和 `body` 参数

### Task 7: 精炼核心（refiner.py）

- **时间：** 2026-08-05
- **Subagent：** OpenCode SDD 工作流
- **产出 commit：** fba9fe2
- **测试结果：** 7/7 通过，全量 62/62 通过
- **评审结果：** ✅ 通过
- **人工干预：** 无
- **修正记录：** 无
- **学到的教训：** 精炼 prompt 模板使用 `{level_instruction}` 占位符，`Refiner` 通过依赖注入 `LLMClient` 接口实现 mock，便于单元测试

### Task 8: CLI 命令（cli.py）

- **时间：** 2026-08-06
- **执行方式：** 手写 TDD（OpenCode 交互式）
- **产出 commit：** 476b489
- **测试结果：** 12/12 通过，全量 74/74 通过
- **评审结果：** ✅ 通过
- **人工干预：** 测试用例中互斥检查需要实际文件路径（click.Path(exists=True) 先校验），修正测试使用 temp_dir fixture
- **学到的教训：** Click 的 `click.Path(exists=True)` 在参数解析阶段校验，互斥逻辑在函数体内，测试需提供真实存在的文件路径

### Task 9: 集成验证

- **时间：** 2026-08-06
- **执行方式：** OpenCode 交互式
- **产出 commit：** ea8dd01
- **测试结果：** 全量 74/74 通过
- **CLI 验证：** `main.py --help`、`refine --help`、`config --help` 正常
- **包安装验证：** `uv pip install -e .` 成功，`notesculpt` CLI 入口正常
- **评审结果：** ✅ 通过
- **人工干预：** 无
- **已知问题：** `config show-status` 在无桌面环境时报 keyring NoKeyringError（运行环境问题，非代码缺陷）
- **学到的教训：** MVP 全部 8 个核心模块 + 74 个测试通过，集成验证完成

### Docker + CI 配置

- **时间：** 2026-08-06
- **执行方式：** OpenCode 交互式
- **产出 commit：** b75aeee（Dockerfile + CI + README），后续补充 build-docker job
- **内容：**
  - Dockerfile：Python 3.11-slim + uv，`.dockerignore` 排除测试/文档
  - CI：`unit-test` job（uv + pytest），`build-docker` job（needs unit-test，setup-buildx + docker build + docker run 验证）
  - README：获取、Docker/本地运行、三级 API Key 配置说明
- **评审结果：** ✅ 通过
- **人工干预：** 无
- **学到的教训：** Docker 镜像中 `[project.scripts]` 入口点需通过 `uv sync` 安装项目才能使用，使用 `.dockerignore` 避免将测试/文档复制进镜像
- **修正记录：** 修复 Docker 镜像中 `notesculpt` 入口点缺失问题。根因是 `uv sync` 默认不安装未显式声明为 package 的项目的 entry points。修正：在 `pyproject.toml` 添加 `[tool.uv] package = true`，并重新生成 `uv.lock`

### GHCR 推送配置

- **时间：** 2026-08-07
- **执行方式：** OpenCode 交互式
- **内容：**
  - CI `build-docker` job 新增 GHCR 登录步骤（`docker/login-action@v3`）
  - 构建并推送镜像到 `ghcr.io/apophisi/notesculpt:latest`
  - 保留本地构建步骤用于 Docker 运行测试
  - README 新增"从 GHCR 拉取"章节
- **评审结果：** 待验证
- **人工干预：** 无

