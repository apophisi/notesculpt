import pytest
from pathlib import Path
from notesculpt.files import discover_files, read_file, output_path, write_file, load_prompt_file
from notesculpt.errors import FileError


class TestDiscoverFiles:
    def test_single_md_file(self, temp_dir):
        md_file = temp_dir / "test.md"
        md_file.write_text("# Hello")
        result = discover_files(md_file)
        assert result == [md_file]

    def test_non_md_file_raises(self, temp_dir):
        txt_file = temp_dir / "test.txt"
        txt_file.write_text("hello")
        with pytest.raises(FileError, match="不是 Markdown 文件"):
            discover_files(txt_file)

    def test_directory_recursive(self, temp_dir):
        (temp_dir / "a.md").write_text("a")
        (temp_dir / "b.md").write_text("b")
        subdir = temp_dir / "sub"
        subdir.mkdir()
        (subdir / "c.md").write_text("c")
        (temp_dir / "ignore.txt").write_text("ignore")

        result = discover_files(temp_dir)
        assert len(result) == 3
        assert result == sorted(result)

    def test_empty_directory_raises(self, temp_dir):
        with pytest.raises(FileError, match="没有找到"):
            discover_files(temp_dir)

    def test_nonexistent_path_raises(self):
        with pytest.raises(FileError, match="路径不存在"):
            discover_files(Path("/nonexistent/path"))


class TestReadFile:
    def test_read_existing_file(self, temp_dir):
        md_file = temp_dir / "test.md"
        md_file.write_text("# Hello World", encoding="utf-8")
        content = read_file(md_file)
        assert content == "# Hello World"

    def test_read_nonexistent_raises(self):
        with pytest.raises(FileError, match="无法读取"):
            read_file(Path("/nonexistent.md"))


class TestOutputPath:
    def test_default_suffix(self, temp_dir):
        input_path = temp_dir / "notes.md"
        result = output_path(input_path)
        assert result == temp_dir / "notes_refined.md"
        assert result.suffix == ".md"

    def test_with_output_dir(self, temp_dir):
        input_path = temp_dir / "notes.md"
        out_dir = temp_dir / "output"
        result = output_path(input_path, output_dir=out_dir)
        assert result == out_dir / "notes_refined.md"

    def test_preserves_stem(self, temp_dir):
        input_path = temp_dir / "my.notes.md"
        result = output_path(input_path)
        assert result.stem == "my.notes_refined"


class TestWriteFile:
    def test_write_creates_file(self, temp_dir):
        out_path = temp_dir / "output.md"
        write_file(out_path, "# Content")
        assert out_path.exists()
        assert out_path.read_text(encoding="utf-8") == "# Content"

    def test_write_creates_parent_dirs(self, temp_dir):
        out_path = temp_dir / "deep" / "nested" / "output.md"
        write_file(out_path, "# Deep")
        assert out_path.exists()
        assert out_path.read_text(encoding="utf-8") == "# Deep"


class TestLoadPromptFile:
    def test_load_prompt_file(self, temp_dir):
        prompt_file = temp_dir / "custom_prompt.txt"
        prompt_file.write_text("请帮我整理笔记", encoding="utf-8")
        content = load_prompt_file(prompt_file)
        assert content == "请帮我整理笔记"

    def test_load_nonexistent_raises(self):
        with pytest.raises(FileError):
            load_prompt_file(Path("/nonexistent.txt"))