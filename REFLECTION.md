# NoteSculpt · 反思报告

## 1. 项目回顾

### 我想解决什么问题？目标用户是谁？

NoteSculpt 解决的核心问题是：**杂乱的学习笔记难以快速回顾和消化**。目标用户是习惯用 Markdown 做学习笔记的学生或知识工作者——他们记了大量笔记，但回头复习时发现内容冗长、结构混乱，缺乏提炼。

### MVP 范围（场景 A）是否合理？有没有在开发过程中发生范围蔓延？

MVP 范围锁定在场景 A（将零散/冗长的学习笔记整理为结构化要点总结），这个决策是正确的。Brainstorming 阶段用户明确将 B（语言润色）和 C（知识图谱）推迟到 v2，开发过程中严格遵守了这个边界。**没有发生范围蔓延**——所有 8 个模块、74 个测试均围绕场景 A 展开，Docker + CI 配置也仅服务于 MVP 分发。

唯一的小例外是 CI 在 MVP 后期增加了 GHCR 推送功能，但这属于"分发"维度的自然延伸，而非功能范围蔓延。

---

## 2. Superpowers 工作流评价

### brainstorming：哪些追问最有价值？哪些地方让你觉得"流程过重"？

**最有价值的追问：**
- 第 1 轮（核心场景确认）：将模糊的"精炼"概念明确为 A/B/C/D 四个具体场景，并精准锁定 MVP 边界
- 第 3 轮（CLI 交互方式）：A+D 组合 + `--in-place`/`--stdout`/`--output-dir` 三个可选参数，设计得相当完整
- 第 5 轮（API Key 配置）：keyring → env → .env 三级优先级链，充分利用了 `keyring` 和 `python-dotenv` 两个已有依赖

**流程过重的地方：**
- 第 7 轮（错误处理）之后感觉可以收尾了，但后续还有 8 轮逐节设计确认。对于 8 个模块的 MVP 项目，7 轮需求澄清 + 8 轮设计确认略显冗长
- 数据模型、错误处理等小模块各占一轮确认，可以合并

### writing-plans：Task 颗粒度（2-5 分钟）在实际执行中是否合适？

PLAN 划分了 9 个 Task，每个 Task 对应一个模块（或脚手架搭建），颗粒度合理。但实际执行中：

- **Task 1（脚手架）** 被冷启动 agent 约 5 分钟完成，OK
- **Task 2-7（models → refiner）** 每个约 10-15 分钟（含写测试 + 实现 + 验证），比预期略长，主要因为 TDD 的"先红再绿"流程增加了步骤
- **Task 8（CLI）** 最复杂，实际约 30 分钟，因为 mock 依赖链较长

整体来看，2-5 分钟的估计偏乐观，实际执行约 10-30 分钟/Task。但 9 个 Task 的划分本身是合理的。

### subagent-driven：智能体能自主运行多久而不偏离？哪些 Task 需要你频繁介入？

**自主运行良好的 Task：**
- Task 3（errors.py）：subagent 完全自主完成了 TDD 循环，仅需修 PEP 8 换行符
- Task 4（config.py）：subagent 自主发现并修正了 keyring 键名不一致（`api_key` → `deepseek_api_key`）
- Task 6（llm.py）：subagent 自主处理了 OpenAI SDK 异常类型的 mock 构造

**需要频繁介入的 Task：**
- Task 2（models.py）和 Task 5（files.py）：subagent 两次将文件写入项目根目录而非 `notesculpt/` 包目录，需要人工移入。根本原因是 PLAN 中的路径约束不够显式
- Task 8（cli.py）：放弃 subagent 改为手写 TDD，因为 Click 参数互斥校验 + mock 依赖链对 subagent 来说过于复杂

**偏离的根本原因：** PLAN 中的"规约不清"——文件路径约束没有作为全局约束放在 PLAN 开头，而是散落在各 Task 的注释中。

### TDD：在 AI 协作下，强制"先红再绿"是阻碍还是放大器？

**是放大器，而非阻碍。** 理由：

1. **防止幻觉代码**：subagent 在没有测试约束时容易生成"看起来对但实际不对"的代码。先写测试等于给 subagent 一个明确的 spec
2. **回归安全网**：Task 4 完成后运行全量 31 个测试，当即发现 Task 3 的 keyring 键名问题，避免了后续连锁 bug
3. **Mock 设计驱动**：config.py 和 llm.py 的测试迫使 mock 设计先行，让依赖注入模式自然浮现
4. **成本**：每个 Task 增加了约 30-50% 的代码量（测试代码），但考虑到 subagent 的偏离风险，这个成本完全值得

---

## 3. AI 协作与 Prompt 工程

### 你最有效的 prompt / context 策略是什么？为什么有效？

1. **AGENTS.md 作为冷启动上下文**：AGENTS.md 明确了 `uv`（非 pip）、Python 3.11、`.venv/` 路径、`.env` gitignored 等关键约束，让每个新 session 的 agent 都能快速进入状态。是最有效的单文件上下文策略

2. **PLAN.md 中的可执行步骤**：每个 Task 的 Step 1-5 结构（写测试 → 验证失败 → 实现 → 验证通过 → 提交）是锁步式的，subagent 无法跳过任何步骤。这比"请实现 config.py"的自由度指令有效得多

3. **依赖注入 + 接口隔离**：Refiner 依赖 LLMClient 接口（而非具体实现），让测试 mock 自然可行。这是设计层面而非 prompt 层面的策略，但极大降低了 AI 生成测试的难度

### 举一个"规约不清导致 subagent 偏离"的具体案例

**案例：Task 2 和 Task 5 的文件路径偏离**

- **规约内容**：PLAN 中每个 Task 写明了"写入 `notesculpt/models.py`"（注意路径前缀），但 subagent 仍将 `models.py` 和 `files.py` 写入项目根目录
- **根本原因**：`notesculpt/` 作为包目录的约束在 PLAN 的"文件结构"树中展示，但 subagent 在实现时忽略了这层嵌套关系，将 `notesculpt/models.py` 理解为相对于项目根目录的路径
- **修正方式**：在 PLAN 中添加了全局约束"源代码目录：`notesculpt/`（Python 包）"，并在 Step 3 中明确加注"注意：文件必须在 notesculpt/ 包目录下，而非项目根目录"
- **教训**：路径约束必须作为 **全局约束** 放在 PLAN 开头，且在每个 Task 的实现步骤中显式重复

另一个案例是 **Docker 入口点缺失**（`pyproject.toml` 缺少 `[tool.uv] package = true`），导致 `uv sync` 不安装项目自身的 entry points。这是 PLAN 中没有覆盖的工程细节。

### 如何在评审中判断 AI 生成的代码是"可接受"还是"需要重写"？

我的评审标准：

| 维度 | 可接受 | 需要重写 |
|------|--------|---------|
| 测试通过 | 全部通过 | 有失败 |
| 接口契约 | 与 PLAN 一致 | 擅自修改接口 |
| 依赖方向 | 符合分层架构 | 反向依赖或循环依赖 |
| 错误处理 | 异常分类正确，边界覆盖 | 吞异常、分类错误 |
| 代码风格 | 与已有代码一致 | 明显风格不一致 |

一个具体例子：Task 3 的 errors.py 实现中，subagent 输出的代码缺少末尾换行符（PEP 8），属于"可接受但需微调"——测试全部通过，逻辑正确，只是风格问题。

---

## 4. 工程实践

### 凭据安全：keyring → env → .env 三级方案在 WSL2 环境下遇到了哪些坑？如何解决的？

**遇到的坑：**

1. **WSL2 无桌面环境导致 keyring NoKeyringError**：在 WSL2 命令行环境下运行 `config show-status` 时，keyring 找不到可用的凭据后端（没有 GNOME Keyring / KDE Wallet / macOS Keychain），抛出 `NoKeyringError`
2. **解决方案**：三级优先级链的设计天然解决了这个问题——当 keyring 不可用时，自动回退到环境变量 `DEEPSEEK_API_KEY` 或 `.env` 文件。在 WSL2 开发环境中，使用 `.env` 文件即可
3. **CI 环境**：GitHub Actions 中使用 `secrets.GHCR_PAT` 而非 keyring，通过环境变量注入

**设计反思**：三级方案在 WSL2 下并非"bug"，而是设计意图——keyring 在最安全的环境（桌面 Linux/macOS/Windows）中工作，在无桌面环境自动降级。这是正确的工程权衡。

### 分发：Docker + GHCR 的 CI 配置过程，暴露了哪些你原本没想到的工程问题？

**问题 1：Docker 镜像中 `notesculpt` 入口点缺失**

- **现象**：Docker 镜像构建成功，但 `docker run notesculpt --help` 报 `exec: "notesculpt": executable file not found`
- **根因**：`uv sync` 默认不安装未显式声明为 package 的项目的 entry points。`pyproject.toml` 缺少 `[tool.uv] package = true`
- **修正**：添加 `[tool.uv] package = true` 并重新生成 `uv.lock`
- **教训**：uv 的 package 模式 vs 非 package 模式的行为差异是隐性知识，文档中不易发现

**问题 2：`.dockerignore` 的必要性**

- 如果不过滤，Docker 构建上下文会包含 `tests/`、`docs/`、`session-*.md` 等开发文件，增加镜像体积
- 解决：添加 `.dockerignore` 排除测试/文档/会话文件

**问题 3：GHCR 认证配置**

- 最初使用 `secrets.GITHUB_TOKEN`，但 GHCR 需要 `packages:write` 权限
- 最终改用 `secrets.GHCR_PAT`（Personal Access Token）
- 镜像标签经过多次迭代：硬编码 `ghcr.io/apophisi/notesculpt:latest` → 尝试使用 `github.repository_owner` 变量 → 最终恢复硬编码（因为 owner 映射关系确定）

**问题 4：CI 中 Docker 构建和推送的分离**

- 需求：推送前先在本地验证镜像可用
- 解决：CI 中两个 `docker/build-push-action` 步骤——第一个 `push: true` 推送到 GHCR，第二个 `load: true` 加载到本地用于 `docker run` 验证

### TDD：这套流程是否让你写出了更可靠的代码？测试覆盖率实际如何？

**是的。** 74 个测试全部通过，覆盖了所有 8 个模块：

| 模块 | 测试数 | 覆盖重点 |
|------|--------|---------|
| models.py | 8 | 字段默认值、类型约束、可选字段 |
| errors.py | 9 | 异常层次结构、退出码 |
| config.py | 13 | 三级优先级链、keyring mock、状态不泄露 |
| files.py | 14 | 文件发现、读写、路径生成、prompt 加载 |
| llm.py | 10 | 重试逻辑、错误分类、空结果、指数退避 |
| refiner.py | 7 | prompt 构建、级别切换、自定义 prompt 覆盖 |
| cli.py | 12 | 参数互斥、输出格式、批量汇总、config 命令 |
| 入口验证 | 1 | `--help` 输出正常 |

**实际效果**：在 Task 4（config.py）完成后运行全量测试，当即发现 Task 3 的 keyring 键名不一致问题（`api_key` vs `deepseek_api_key`）。如果没有这层回归安全网，这个 bug 可能到 Task 8（CLI 集成）才暴露，定位成本高得多。

---

## 5. 批判性反思

### Superpowers 假设了"AI 能理解并遵循流程"，这个假设在你的项目里成立吗？

**部分成立，但不完全。**

- **成立的部分**：AI 能够理解 brainstorming 的逐轮提问模式、writing-plans 的 Task 分解结构、TDD 的"先红再绿"循环。这些流程都是结构化的、可模板化的，恰好在 AI 的能力边界内
- **不成立的部分**：AI 在细节层面频繁偏离，需要人工修正：
  - 文件路径（两次写入根目录）
  - keyring 键名（大小写不一致）
  - Docker 入口点（uv package 模式）
  - 这些偏离的共同特征是：**隐式知识**（如"Python 包目录 = 嵌套文件夹"、"uv 的 package 模式"）而非显式规则

**核心矛盾**：Superpowers 流程假设 AI 能"理解"任务，但实际上 AI 是在"模式匹配"——当 PLAN 中的模式与 AI 的内置知识冲突时，AI 倾向于遵循内置知识（如"Python 文件放在项目根目录"），而非 PLAN 中的显式指令。

### 如果重做，你会在哪个环节改变策略？为什么？

1. **PLAN 中增加全局约束章节**：将文件路径、包结构、命名约定等全局约束放在 PLAN 最前面，以粗体/大写强调。当前这些约束散落在各 Task 中，subagent 容易忽略

2. **Task 8（CLI）仍用手写 TDD**：这个决策是正确的，subagent 在处理多层 mock + Click 参数校验时容易失控。对于依赖链复杂的模块，手写 TDD 比 subagent 更高效

3. **Brainstorming 可以精简 2-3 轮**：7 轮需求澄清 + 8 轮设计确认对 MVP 规模的项目偏多。可以将数据模型、错误处理、配置管理合并为 1-2 轮确认

4. **Docker 配置应该在 PLAN 中**：当前 Docker + CI 是 PLAN 之外的"追加任务"，导致 CI 配置经历了多次迭代（GHCR 认证、镜像标签、入口点缺失）。如果一开始就纳入 PLAN，可以避免反复试错

### 你认为这份作业最想训练的能力是什么？你觉得自己在这方面有进步吗？

**最想训练的能力：AI 协作下的工程纪律**——不是"让 AI 写代码"，而是"让 AI 在严格的工程约束下写代码"。

具体包括：
- 用 brainstorming 收敛需求，防止范围蔓延
- 用 writing-plans 将需求转化为可执行的锁步计划
- 用 TDD 给 AI 一个不可绕过的验证机制
- 用 subagent 实现并行开发，用 code review 守住质量
- 用 Docker + CI 完成从代码到分发的完整链路

**进步**：从最初"让 AI 自由发挥"到后来"给 AI 精确的锁步指令 + 测试验证"，对 AI 能力的边界理解更清晰了。AI 擅长模式匹配和模板化工作，但不擅长需要全局上下文的决策（如文件路径约定、包结构设计）。好的工程纪律就是把决策权留给人，把执行权交给 AI。

---

## 6. 总结

### 用一段话总结你对 AI4SE 的核心理解

AI4SE（AI for Software Engineering）的本质不是"AI 替代工程师"，而是"AI 成为工程师的加速器"——它的价值在于以极低成本覆盖"已知-已知"的模板化工作（写测试、实现约定接口、配置 CI），释放工程师的精力去处理"已知-未知"的决策工作（需求收敛、架构权衡、边界条件判断）。但前提是工程师必须建立严格的工程纪律：brainstorming 收敛需求、writing-plans 固化决策、TDD 提供验证闭环、code review 守住质量。没有这些纪律，AI 的效率会被偏离和失误吞噬；有了这些纪律，AI 可以成为 10x 放大器。