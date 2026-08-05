from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal


@dataclass
class Config:
    api_key: str
    base_url: str = "https://api.deepseek.com/v1"
    model: str = "deepseek-chat"


@dataclass
class RefineRequest:
    content: str
    file_path: Path
    level: Literal["brief", "moderate", "detailed"]
    custom_prompt: str | None = None


@dataclass
class RefineResult:
    original_content: str
    refined_content: str
    original_chars: int
    refined_chars: int
    level: str
    timestamp: datetime


@dataclass
class BatchResult:
    success_count: int
    failure_count: int
    failures: list[tuple[Path, str]]
    elapsed_seconds: float