# NoteSculpt · 规约过程文档

> 记录与 Superpowers 协作生成 SPEC 与 PLAN 的过程，以及设计验证的发现与修正。

---

## 1. 对话轮次记录

### 第 1 轮：核心场景确认

**智能体提问：** 你期望 NoteSculpt 主要解决什么笔记场景？

选项：
- A. 将零散/冗长的会议/学习笔记整理成结构化的要点总结
- B. 对已有的笔记进行语言润色、格式修正、术语统一
- C. 从多篇笔记中提取共性、关联知识点，生成知识图谱式输出
- D. 以上都包含，做一个通用的笔记精炼工具

**用户回答：** 选择 D，但优先级是：先做好 A（将零散/冗长的学习笔记整理成结构化的要点总结），B 和 C 作为 v2 扩展功能。当前 MVP 只做 A。

具体核心能力：
1. 输入：一篇杂乱的学习笔记（Markdown 格式）
2. 处理：识别冗余内容、提取核心观点、重组逻辑结构
3. 输出：结构清晰、重点突出的精炼笔记

**采纳/推翻：** 采纳了 D 的愿景，但将范围明确收缩为 A 作为 MVP。这为后续所有设计决策设定了边界。


### 第 2 轮：LLM 提供商选择

**智能体提问：** 你倾向使用哪个 LLM 提供商？

选项：
- A. OpenAI（GPT-4o / GPT-4o-mini）
- B. Anthropic（Claude）
- C. 本地模型（Ollama / llama.cpp 等）
- D. 支持多个提供商，通过配置文件切换

**用户回答：** 选择 DeepSeek API。

理由：
1. API 格式与 OpenAI 兼容，可以用 OpenAI SDK 直接调用，省去适配成本
2. 成本显著低于 OpenAI，适合在课程项目期间大量测试
3. 中文处理能力强，适合笔记精炼这个中文场景
4. 有免费额度，足够项目开发和测试使用

技术实现：
- 使用 OpenAI SDK（`openai` 包），base_url 指向 DeepSeek API
- 模型选择：`deepseek-chat`（主力）或 `deepseek-reasoner`（如需更精细的重构）
- API Key 通过 keyring 安全存储
- 支持通过 CLI 参数或配置文件切换模型（方便未来切换到其他兼容 API）

**采纳/推翻：** 采纳了 OpenAI SDK 兼容方案。智能体确认了"需要显式传 base_url 和 api_key"。


### 第 3 轮：CLI 交互方式

**智能体提问：** 你期望的命令行交互方式是什么？

选项：
- A. 单文件处理：生成 `_refined` 后缀新文件
- B. 原地覆盖：直接修改输入文件
- C. 输出到 stdout：打印到终端
- D. 批量处理：扫描目录下所有 `.md` 文件

**用户回答：** 选择 A + D 组合，加上两个可选参数。

默认行为：
- 单文件：`notesculpt refine my-notes.md` → 同目录生成 `my-notes_refined.md`
- 批量：`notesculpt refine notes/` → 递归扫描所有 `.md`，每个生成对应 `_refined` 版本

可选参数：
- `--in-place`：原地覆盖原文件（加确认提示）
- `--stdout`：打印到终端（方便预览/管道操作）
- `--output-dir <dir>`：指定输出目录

**采纳/推翻：** 全部采纳。智能体确认了"精炼过程的用户可控性"作为下一个问题方向。


### 第 4 轮：精炼控制选项

**智能体提问：** 精炼过程的用户可控性如何？你希望支持哪些自定义选项？

选项：
- A. 零配置：完全自动
- B. 简洁度控制：`--level` 参数
- C. 自定义 Prompt：`--prompt` 或 `--prompt-file`
- D. 全部都要：`--level` + 自定义 prompt + 高级参数

**用户回答：** 选择 B + C 组合。

MVP 精炼控制：
- `--level`：brief（极度精简）/ moderate（中度精炼，默认）/ detailed（轻度整理）
- `--prompt-file`：用户自定义精炼指令文件，覆盖默认精炼指令

暂不包含（v2 扩展）：
- `--temperature`：暂不暴露，使用固定值 0.3-0.5
- `--preserve-topics`：暂不实现
- 交互式精炼：暂不实现

**采纳/推翻：** 采纳了 B + C。智能体建议的 `--temperature`、`--preserve-topics` 被明确推迟到 v2。用户给出的理由：避免过度设计，保持 CLI 参数简洁，同时展示可配置性维度。


### 第 5 轮：API Key 配置方式

**智能体提问：** API Key 的配置方式你偏好哪种？

选项：
- A. 纯 keyring
- B. 纯环境变量/`.env`
- C. 混合方案：优先 keyring → 回退到环境变量 → 回退到 `.env`
- D. C 方案基础上 + `--api-key` CLI 参数 + `config.toml` 配置文件

**用户回答：** 选择 C 方案。

优先级链：
1. keyring（最安全）
2. 环境变量 `DEEPSEEK_API_KEY`（便于 CI/CD）
3. `.env` 文件（便于本地开发）

配套命令：
- `notesculpt config set-key`
- `notesculpt config delete-key`
- `notesculpt config show-status`（不泄露 key）

暂不包含（v2 扩展）：
- `--api-key` CLI 参数（会出现在 shell history 中，安全风险）
- `~/.config/notesculpt/config.toml`（避免配置文件格式复杂度）

**采纳/推翻：** 采纳了 C。智能体建议的 `--api-key` 和 `config.toml` 被明确拒绝（安全风险 + 过度设计）。


### 第 6 轮：输出格式与结构

**智能体提问：** 精炼输出的格式和结构有什么要求？

选项：
- A. 纯 Markdown
- B. 增强 Markdown（加入元信息块）
- C. B + YAML front matter

**用户回答：** 选择 B（增强 Markdown），精炼结构使用"自定义模板"方式。

元信息块（Markdown 引用块，放在顶部）：
- 精炼时间
- 原始字数 / 精炼后字数
- 精炼级别
- 压缩比

精炼结构（半固定模板 + LLM 自适应）：
- 固定部分：总是包含"核心摘要"和"要点总结"
- 自适应部分：LLM 根据内容自行决定（关键概念、行动项、问题与思考等）

**采纳/推翻：** 采纳了 B。智能体建议的 YAML front matter（选项 C）被跳过，用户选择了更简洁的 Markdown 引用块方案。


### 第 7 轮：错误处理策略

**智能体提问：** LLM 调用失败时，你期望的错误处理策略是什么？

选项：
- A. 简单失败：报错退出
- B. 自动重试：最多 3 次，指数退避
- C. B + 批量模式部分成功
- D. C + 写入缓存/断点续传

**用户回答：** 选择 B + C 组合。

自动重试（B）：
- 最多 3 次，指数退避（1s → 2s → 4s）
- 仅重试可恢复错误（网络超时、429、5xx）
- 不可恢复错误（401、400）立即失败

批量模式容错（C）：
- 单个文件失败不中断整体流程
- 汇总报告：成功数/失败数/失败文件列表

暂不包含（v2 扩展）：
- 失败缓存/断点续传（D）
- 详细错误日志文件

**采纳/推翻：** 采纳了 B + C。智能体建议的 D（断点续传）被推迟到 v2。


### 第 8 轮：架构方案选择

**智能体提议：** 三种架构方案：
- A. 单文件命令式（最简单，但不可测试）
- B. 分层架构（8 个模块，清晰分层，推荐）
- C. 插件式架构（过度设计）

**用户回答：** 选择方案 B（分层架构），8 个模块：`cli.py`、`refiner.py`、`llm.py`、`config.py`、`files.py`、`models.py`、`errors.py`、`main.py`。

理由：
1. 分层清晰，每层职责单一，符合 TDD 要求
2. 文件数量（~8 个）在 MVP 阶段完全可控
3. 为 v2 扩展预留了清晰的接口边界
4. 工程深度适中

**采纳/推翻：** 采纳了方案 B。智能体推荐的方案正是方案 B，用户与智能体意见一致。方案 A（单文件）和方案 C（插件式）被明确否决——前者不可测试，后者过度设计。


### 第 9 轮：数据模型设计

**智能体提议：** 使用 `dataclass` 定义 4 个模型：`Config`、`RefineRequest`、`RefineResult`、`BatchResult`。

**用户回答：** 确认通过。

建议优化（采纳）：
- `RefineRequest.level` 使用 `Literal["brief", "moderate", "detailed"]` 类型提示

**采纳/推翻：** 设计确认，Literal 类型提示建议被采纳。


### 第 10 轮：错误处理设计

**智能体提议：** 异常层次结构：`NoteSculptError` → `RetryableError`（`RateLimitError`/`NetworkError`/`ServerError`）和 `FatalError`（`AuthError`/`ConfigError`/`FileError`），每个错误带 `exit_code`。

**用户回答：** 确认通过。

建议优化（推迟到 v2）：
- `RateLimitError` 增加 `retry_after` 字段，使用服务端建议的等待时间

**采纳/推翻：** 设计确认，`retry_after` 建议被推迟到 v2。


### 第 11 轮：配置管理设计

**智能体提议：** `ConfigLoader` 类，实现三级优先级链（keyring → env → `.env`），使用 `dotenv_values()` 而非 `load_dotenv()` 避免污染 `os.environ`。

**用户回答：** 确认通过。

建议优化（标记为可选）：
- `set_key()` 后验证 API Key 是否有效（调用轻量 API）

**采纳/推翻：** 设计确认，验证建议被标记为可选，不强制实现。


### 第 12 轮：LLM 客户端设计

**智能体提议：** `LLMClient` 封装 OpenAI SDK，内置重试（3 次、指数退避）、错误分类（映射 OpenAI SDK 异常到 NoteSculpt 异常）、固定 `temperature=0.3`。

**用户回答：** 确认通过。

建议优化（采纳）：
- 检查 `response.choices[0].message.content` 是否为空，为空时抛出 `FatalError`

**采纳/推翻：** 设计确认，空结果检查建议被采纳。


### 第 13 轮：文件 I/O 设计

**智能体提议：** 5 个工具函数：`discover_files()`、`read_file()`、`output_path()`、`write_file()`、`load_prompt_file()`。仅支持 `.md` 扩展名。

**用户回答：** 确认通过。

建议优化（推迟到 v2）：
- 是否支持 `.markdown` 扩展名？→ MVP 仅 `.md`

**采纳/推翻：** 设计确认，`.markdown` 支持被推迟到 v2。


### 第 14 轮：精炼核心设计

**智能体提议：** `Refiner` 类，依赖注入 `LLMClient`。内置默认 prompt 模板（核心摘要 + 要点总结 + 自适应章节），`--prompt-file` 完全覆盖默认 prompt。三种精炼级别对应不同 prompt 描述。

**用户回答：** 确认通过。

建议优化（推迟到 v2）：
- 在 prompt 中加入篇幅比例参考（brief 30-40%、moderate 50-60%）
- 在 `RefineResult` 中标记生成了哪些章节

**采纳/推翻：** 设计确认，篇幅比例建议在设计文档中已体现，章节标记推迟到 v2。


### 第 15 轮：CLI 命令层设计

**智能体提议：** 命令结构：`notesculpt refine` + `notesculpt config` 子命令组。参数互斥检查在 CLI 层处理。`format_output()` 独立函数生成元信息块。`main.py` 保持极简入口。

**用户回答：** 确认通过。

**采纳/推翻：** 设计确认，无修改意见。


### 第 16 轮：规格文档评审

**智能体：** 完成 `docs/superpowers/specs/2026-08-04-notesculpt-design.md`，自审后修正了 `--in-place` 确认提示和 `load_prompt_file` 职责两个小问题。

**用户回答：** 评审通过，无修改意见。

**采纳/推翻：** 规格文档确认通过。


---

## 2. 决策总结

### 用户采纳的智能体建议

| 建议 | 轮次 | 采纳状态 |
|------|------|---------|
| 分层架构（方案 B）替代单文件和插件式 | 8 | ✅ 采纳 |
| `Literal` 类型提示用于 `level` 字段 | 9 | ✅ 采纳 |
| 空结果检查（LLM 返回空内容时抛异常） | 12 | ✅ 采纳 |
| 使用 `dotenv_values()` 而非 `load_dotenv()` | 11 | ✅ 采纳（设计阶段） |
| `--in-place` 添加确认提示 | 15 | ✅ 采纳 |
| `load_prompt_file` 纳入 files.py 职责 | 15 | ✅ 采纳 |

### 用户拒绝或推迟的智能体建议

| 建议 | 轮次 | 状态 | 原因 |
|------|------|------|------|
| YAML front matter 元数据 | 6 | ❌ 跳过 | 选择更简洁的 Markdown 引用块 |
| `--temperature` 参数 | 4 | ⏸️ v2 | 避免过度设计，MVP 固定值 |
| `--preserve-topics` 参数 | 4 | ⏸️ v2 | 避免过度设计 |
| 交互式精炼 | 4 | ⏸️ v2 | 增加复杂度 |
| `--api-key` CLI 参数 | 5 | ❌ 拒绝 | 安全风险（shell history） |
| `config.toml` 配置文件 | 5 | ⏸️ v2 | 优先级链已足够 |
| 断点续传 / 失败缓存 | 7 | ⏸️ v2 | 增加复杂度 |
| 插件式架构（方案 C） | 8 | ❌ 拒绝 | 过度设计 |
| `retry_after` 字段 | 10 | ⏸️ v2 | 进阶优化 |
| `set_key()` 后验证 API Key | 11 | ⏸️ 可选 | 友好性优化，非必需 |
| `.markdown` 扩展名支持 | 13 | ⏸️ v2 | 边缘场景 |
| 篇幅比例参考在 prompt 中 | 14 | ⏸️ v2 | 已体现在设计文档中 |

### 用户主动提出的关键决策

| 决策 | 轮次 |
|------|------|
| MVP 仅做场景 A（笔记精炼），B/C 为 v2 | 1 |
| 选择 DeepSeek API（成本、中文能力、兼容性） | 2 |
| 使用 OpenAI SDK 兼容模式调用 DeepSeek | 2 |
| 三级优先级链（keyring → env → .env） | 5 |
| 半固定模板 + LLM 自适应输出结构 | 6 |
| 指数退避重试策略（1s → 2s → 4s） | 7 |
| 不可恢复错误立即失败，不重试 | 7 |
| 输出元信息块使用 Markdown 引用块格式 | 6 |


---

## 3. 设计验证

### 3.1 冷启动验证（Task 1-2）

#### 验证设置

- **验证时间：** 2026-08-05
- **主开发 agent：** OpenCode + DeepSeek V4 Pro
- **验证用 agent：** OpenCode（全新 session，无历史上下文）
- **选取的 Task：** Task 1（脚手架）+ Task 2（数据模型）

#### 验证过程记录

**agent 在哪里暂停并提问：**
- **未提问**——它直接执行了，没有暂停询问。这说明：虽然 SPEC 有歧义，但 agent 选择「先做，遇到问题再修正」，而非「停下来问」。

**暴露的 spec 缺陷：**
- PLAN.md 中 Task 2 Step 3 未明确 `models.py` 的文件路径，导致 agent 将文件写入项目根目录而非 `notesculpt/` 包内。

**与预期不一致的解读：**
- 新 agent 理解「实现 models.py」为「在根目录创建 models.py」，而非「在 notesculpt/ 包内创建 models.py」。

#### 产出与修正

**修正前的 PLAN 片段：**
□ Step 3: 实现 models.py
text

**修正后的 PLAN 片段：**
□ Step 3: 实现 notesculpt/models.py
注意：文件必须在 notesculpt/ 包目录下，而非项目根目录。
text

**修正 commit：** `12573b6`


### 3.2 正式实现验证

#### Task 3 验证结论

- 异常层次结构设计合理，agent 完全按照 SPEC 实现
- 退出码分配正确（AuthError=2, ConfigError=3, FileError=4）
- `Literal` 类型提示被正确使用
- 9 个测试全部通过，覆盖所有异常类型和继承关系

#### Task 4 验证结论

- 配置管理三级优先级链（keyring → env → .env）正确实现
- `dotenv_values()` 正确使用，未污染 `os.environ`
- `get_status()` 不泄露 key 值，符合安全要求
- 测试修正：测试 mock 中的 keyring 键名从 `"api_key"` 改为 `"deepseek_api_key"`，匹配 `_resolve()` 中 `key.lower()` 的行为
- 13 个测试全部通过，全量测试 31/31 通过，无回归

#### Task 5 验证结论

- 5 个文件 I/O 工具函数全部正确实现：`discover_files`、`read_file`、`output_path`、`write_file`、`load_prompt_file`
- 所有 I/O 错误正确封装为 `FileError`
- 14 个测试全部通过，覆盖正常路径、边界条件、错误路径
- 全量测试 45/45 通过，无回归
- **注意：** `files.py` 再次被写入项目根目录，Subagent 自行修正。此问题与 Task 2 相同模式，说明 PLAN 中的路径约束仍不够显式。

#### Task 6 验证结论

- LLM 客户端正确封装 OpenAI SDK，`base_url` 指向 DeepSeek API
- 重试逻辑：最多 3 次，指数退避 1s→2s→4s，仅对 `RetryableError` 子类触发
- 错误分类映射正确：`AuthenticationError`→`AuthError`、`RateLimitError`→`RateLimitError`、`APIConnectionError`/`APITimeoutError`→`NetworkError`、`APIStatusError`(5xx)→`ServerError`
- 空结果检查：`content` 为空或 `None` 时抛出 `FatalError`
- `temperature=0.3` 固定内置，不暴露为参数
- 10 个测试全部通过，包括正常调用、参数验证、空结果、重试逻辑、指数退避验证、重试耗尽、不可恢复错误立即失败
- 全量测试 55/55 通过，无回归

### 3.3 验证反思

> 冷启动验证让我意识到：**PLAN.md 中每个 Task 的「涉及文件」字段需要更加明确**。虽然 SPEC 的「架构设计」一节列出了完整目录树，但 PLAN 作为子 agent 执行时的主要参考，需要在每个步骤中显式写出文件路径。

**设计验证的总体结论：**
- SPEC 中 8 个模块的数据模型、错误处理、配置管理设计在实践中验证通过
- 文件路径歧义是唯一暴露的问题，已在冷启动阶段修正
- Task 3-6 的顺利执行表明修正后的 PLAN 质量达到预期
- PLAN 中的测试代码与实际实现之间可能存在细微不一致（如 keyring 键名），但 Subagent 具备自行发现并修正的能力


---

## 4. 修订历史

| 日期 | 修订内容 | 触发原因 |
|------|---------|---------|
| 2026-08-04 | SPEC.md 初始版本 | Brainstorming 完成 |
| 2026-08-04 | PLAN.md 初始版本 | Writing-Plans 完成 |
| 2026-08-05 | PLAN.md Task 2 Step 3 补充文件路径 | 冷启动验证暴露歧义 |
| 2026-08-05 | SPEC.md 架构设计补充目录结构说明 | 冷启动验证暴露歧义 |
| 2026-08-05 | 添加冷启动验证记录 | 冷启动验证完成 |
| 2026-08-05 | 添加 Task 3 验证记录 | Task 3 实现完成 |
| 2026-08-05 | 添加 Task 4 验证记录 | Task 4 实现完成 |
| 2026-08-05 | 添加 Task 5 验证记录 | Task 5 实现完成 |
| 2026-08-05 | 添加 Task 6 验证记录 | Task 6 实现完成 |