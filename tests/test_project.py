from pathlib import Path

import pytest

from cliptranslate.core import Caption, ClipError, VideoInfo
from cliptranslate.project import load_project, save_project


def test_save_and_reopen_local_editable_draft(tmp_path: Path):
    video = VideoInfo(tmp_path / "le film.mp4", 9.6, 4096, True)
    captions = [Caption(0.2, 2.1, "Good morning!"), Caption(2.2, 5, "I'm ready.")]
    destination = tmp_path / "saved.cliptranslate.json"
    save_project(destination, video, captions, "small", 27.5)
    draft = load_project(destination)
    assert draft.video_path == video.path
    assert draft.video_size == video.size
    assert draft.model_size == "small"
    assert draft.processing_seconds == 27.5
    assert draft.captions == captions


def test_rejects_corrupt_or_unsafe_project(tmp_path: Path):
    path = tmp_path / "bad.cliptranslate.json"
    path.write_text("not JSON", encoding="utf-8")
    with pytest.raises(ClipError, match="Could not open"):
        load_project(path)
    with pytest.raises(ClipError, match="empty"):
        save_project(
            path,
            VideoInfo(Path("sample.mp4"), 2, 12, True),
            [Caption(0, 1, "")],
            "base",
            0,
        )
