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