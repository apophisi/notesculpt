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