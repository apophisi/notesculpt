# SPEC_PROCESS.md - NoteSculpt 规格过程记录

## 项目概述

NoteSculpt 是一个智能笔记精炼器，通过 DeepSeek LLM 将杂乱的 Markdown 学习笔记精炼为结构清晰、重点突出的版本。

## 版本历史

### v1.0.0 - MVP

- **日期：** 2026-08-05 ~ 2026-08-06
- **范围：** 核心功能实现
- **模块：** models.py, errors.py, config.py, files.py, llm.py, refiner.py, cli.py
- **测试：** 74 个测试全部通过
- **分发：** Docker 容器 + CI 自动构建

### v1.0.1 - GHCR 推送

- **日期：** 2026-08-07
- **范围：** CI 增强，支持 GHCR 推送
- **变更：**
  - CI 新增 GHCR 登录和镜像推送步骤
  - README 新增 GHCR 拉取说明

## 技术决策

| 决策 | 理由 |
|------|------|
| 使用 uv 作为包管理器 | 快速、现代，项目要求 |
| 使用 click 作为 CLI 框架 | 成熟稳定，强大的参数解析 |
| 使用 keyring 存储 API Key | 操作系统级安全存储 |
| 使用 python-dotenv 加载环境变量 | 支持 Docker/CI 场景 |
| 使用 Docker 分发 | 跨平台兼容，无需安装 Python |
| 使用 GHCR 存储镜像 | 与 GitHub 生态集成，免费 |
| 使用 pytest 测试框架 | 简洁强大，项目要求 |

## 待办事项

- [ ] 添加代码检查（lint）和类型检查（typecheck）工具
- [ ] 添加更多 LLM 提供商支持（如 OpenAI、Claude）
- [ ] 支持更多输出格式（PDF、HTML）
- [ ] 添加 GUI 界面