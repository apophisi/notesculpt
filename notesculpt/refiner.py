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