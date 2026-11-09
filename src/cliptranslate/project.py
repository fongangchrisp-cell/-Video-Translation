"""Small, local, editable project files; never store model weights or copied video."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from .core import Caption, ClipError, VideoInfo, validate_captions

PROJECT_VERSION = 1
_FINGERPRINT_BLOCK = 1024 * 1024


def video_fingerprint(path: Path) -> str:
    """Identify a video by size plus its first and last megabyte (fast, no full read)."""
    path = Path(path)
    size = path.stat().st_size
    digest = hashlib.sha256(str(size).encode())
    with path.open("rb") as file:
        digest.update(file.read(_FINGERPRINT_BLOCK))
        if size > 2 * _FINGERPRINT_BLOCK:
            file.seek(size - _FINGERPRINT_BLOCK)
            digest.update(file.read(_FINGERPRINT_BLOCK))
    return digest.hexdigest()


@dataclass(frozen=True)
class Project:
    video_path: Path
    video_size: int
    video_duration: float
    model_size: str
    processing_seconds: float
    captions: list[Caption]
    video_fingerprint: str = ""


def save_project(
    path: Path,
    video: VideoInfo,
    captions: Sequence[Caption],
    model_size: str,
    processing_seconds: float,
) -> Path:
    path = Path(path).expanduser().resolve()
    if not path.name.endswith(".cliptranslate.json"):
        raise ClipError("Project files must end in .cliptranslate.json.")
    validate_captions(captions, video.duration)
    data = {
        "version": PROJECT_VERSION,
        "source_language": "fr",
        "target_language": "en",
        "video_path": str(video.path),
        "video_fingerprint": _safe_fingerprint(video.path),
        "video_size": video.size,
        "video_duration": video.duration,
        "model_size": model_size,
        "processing_seconds": processing_seconds,
        "captions": [
            {
                "start": item.start,
                "end": item.end,
                "english": item.english,
                "french": item.french,
            }
            for item in captions
        ],
    }
    temporary: Path | None = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=".cliptranslate-",
            suffix=".json",
            delete=False,
        ) as file:
            temporary = Path(file.name)
            json.dump(data, file, ensure_ascii=False, indent=2)
            file.write("\n")
        os.replace(temporary, path)
    except OSError as exc:
        raise ClipError(f"Could not save the project: {exc}") from exc
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return path


def _safe_fingerprint(path: Path) -> str:
    try:
        return video_fingerprint(path)
    except OSError:
        return ""


def load_project(path: Path) -> Project:
    try:
        path = Path(path).expanduser().resolve()
        if path.stat().st_size > 5 * 1024 * 1024:
            raise ClipError("That project file is unexpectedly large.")
        data = json.loads(path.read_text(encoding="utf-8"))
        if data["version"] != PROJECT_VERSION or (
            data["source_language"],
            data["target_language"],
        ) != ("fr", "en"):
            raise ClipError("This project is not a supported French-to-English pilot project.")
        captions = [
            Caption(
                float(item["start"]),
                float(item["end"]),
                str(item["english"]),
                str(item.get("french", "")),
            )
            for item in data["captions"]
        ]
        duration = float(data["video_duration"])
        validate_captions(captions, duration)
        return Project(
            video_path=Path(data["video_path"]),
            video_size=int(data["video_size"]),
            video_duration=duration,
            model_size=str(data["model_size"]),
            processing_seconds=float(data["processing_seconds"]),
            captions=captions,
            video_fingerprint=str(data.get("video_fingerprint", "")),
        )
    except ClipError:
        raise
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        raise ClipError(f"Could not open this project file: {exc}") from exc
