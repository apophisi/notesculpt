import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from notesculpt.cli import cli, format_output
from notesculpt.models import RefineResult


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def sample_result():
    return RefineResult(
        original_content="原始内容很长" * 100,
        refined_content="## 核心摘要\n\n精炼后的内容",
        original_chars=700,
        refined_chars=18,
        level="moderate",
        timestamp=datetime(2026, 8, 4, 14, 30, 0),
    )


class TestConfigCommands:
    def test_show_status(self, runner):
        with patch("notesculpt.cli.ConfigLoader") as mock_loader_class:
            mock_loader = MagicMock()
            mock_loader.get_status.return_value = {
                "key_configured": True,
                "model": "deepseek-chat",
                "base_url": "https://api.deepseek.com/v1",
            }
            mock_loader_class.return_value = mock_loader

            result = runner.invoke(cli, ["config", "show-status"])
            assert result.exit_code == 0
            assert "API Key" in result.output
            assert "deepseek-chat" in result.output

    def test_set_key_prompts(self, runner):
        with patch("notesculpt.cli.ConfigLoader") as mock_loader_class:
            mock_loader = MagicMock()
            mock_loader_class.return_value = mock_loader

            result = runner.invoke(cli, ["config", "set-key"], input="sk-test-key\n")
            assert result.exit_code == 0
            mock_loader.set_key.assert_called_once_with("sk-test-key")


class TestRefineCommand:
    def test_refine_help(self, runner):
        result = runner.invoke(cli, ["refine", "--help"])
        assert result.exit_code == 0
        assert "--level" in result.output
        assert "--in-place" in result.output
        assert "--stdout" in result.output
        assert "--output-dir" in result.output

    def test_refine_in_place_and_stdout_mutually_exclusive(self, runner, temp_dir):
        md_file = temp_dir / "test.md"
        md_file.write_text("# Test")
        result = runner.invoke(
            cli, ["refine", str(md_file), "--in-place", "--stdout"]
        )
        assert result.exit_code != 0
        assert "不能同时使用" in result.output

    def test_refine_in_place_and_output_dir_mutually_exclusive(self, runner, temp_dir):
        md_file = temp_dir / "test.md"
        md_file.write_text("# Test")
        result = runner.invoke(
            cli, ["refine", str(md_file), "--in-place", "--output-dir", "./out"]
        )
        assert result.exit_code != 0
        assert "不能同时使用" in result.output

    def test_refine_invalid_level(self, runner, temp_dir):
        md_file = temp_dir / "test.md"
        md_file.write_text("# Test")
        result = runner.invoke(cli, ["refine", str(md_file), "--level", "invalid"])
        assert result.exit_code != 0

    def test_refine_single_file(self, runner, temp_dir, sample_result):
        md_file = temp_dir / "test.md"
        md_file.write_text("# Test content")

        with patch("notesculpt.cli.ConfigLoader") as mock_cfg_class:
            mock_cfg = MagicMock()
            mock_cfg.load.return_value = MagicMock()
            mock_cfg_class.return_value = mock_cfg
            with patch("notesculpt.cli.LLMClient"):
                with patch("notesculpt.cli.Refiner") as mock_refiner_class:
                    mock_refiner = MagicMock()
                    mock_refiner.refine.return_value = sample_result
                    mock_refiner_class.return_value = mock_refiner

                    result = runner.invoke(cli, ["refine", str(md_file)])
                    assert result.exit_code == 0
                    assert (temp_dir / "test_refined.md").exists()

    def test_refine_stdout(self, runner, temp_dir, sample_result):
        md_file = temp_dir / "test.md"
        md_file.write_text("# Test content")

        with patch("notesculpt.cli.ConfigLoader") as mock_cfg_class:
            mock_cfg = MagicMock()
            mock_cfg.load.return_value = MagicMock()
            mock_cfg_class.return_value = mock_cfg
            with patch("notesculpt.cli.LLMClient"):
                with patch("notesculpt.cli.Refiner") as mock_refiner_class:
                    mock_refiner = MagicMock()
                    mock_refiner.refine.return_value = sample_result
                    mock_refiner_class.return_value = mock_refiner

                    result = runner.invoke(cli, ["refine", str(md_file), "--stdout"])
                    assert result.exit_code == 0
                    assert "核心摘要" in result.output
                    assert "精炼信息" in result.output

    def test_refine_batch_shows_summary(self, runner, temp_dir, sample_result):
        (temp_dir / "a.md").write_text("# A")
        (temp_dir / "b.md").write_text("# B")

        with patch("notesculpt.cli.ConfigLoader") as mock_cfg_class:
            mock_cfg = MagicMock()
            mock_cfg.load.return_value = MagicMock()
            mock_cfg_class.return_value = mock_cfg
            with patch("notesculpt.cli.LLMClient"):
                with patch("notesculpt.cli.Refiner") as mock_refiner_class:
                    mock_refiner = MagicMock()
                    mock_refiner.refine.return_value = sample_result
                    mock_refiner_class.return_value = mock_refiner

                    result = runner.invoke(cli, ["refine", str(temp_dir)])
                    assert result.exit_code == 0
                    assert "批量处理完成" in result.output
                    assert "成功" in result.output


class TestFormatOutput:
    def test_format_output_includes_metadata(self, sample_result):
        output = format_output(sample_result)
        assert "精炼信息" in output
        assert "2026-08-04 14:30:00" in output
        assert "moderate" in output
        assert "压缩比" in output
        assert "核心摘要" in output

    def test_format_output_calculates_ratio(self, sample_result):
        output = format_output(sample_result)
        assert "97%" in output

    def test_format_output_includes_refined_content(self, sample_result):
        output = format_output(sample_result)
        assert "精炼后的内容" in output