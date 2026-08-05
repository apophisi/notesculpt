from pathlib import Path
from notesculpt.errors import FileError

SUFFIX = "_refined"


def discover_files(path: Path) -> list[Path]:
    if not path.exists():
        raise FileError(f"路径不存在: {path}")
    if path.is_file():
        if path.suffix != ".md":
            raise FileError(f"不是 Markdown 文件: {path}")
        return [path]
    if path.is_dir():
        files = sorted(path.rglob("*.md"))
        if not files:
            raise FileError(f"目录中没有找到 .md 文件: {path}")
        return files
    raise FileError(f"路径不存在: {path}")


def read_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        raise FileError(f"无法读取文件 {path}: {e}")


def output_path(input_path: Path, output_dir: Path | None = None) -> Path:
    base = output_dir or input_path.parent
    return base / f"{input_path.stem}{SUFFIX}.md"


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def load_prompt_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        raise FileError(f"无法读取 prompt 文件 {path}: {e}")