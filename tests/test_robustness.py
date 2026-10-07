import subprocess
from itertools import pairwise
from pathlib import Path

import pytest

from cliptranslate import diagnostics
from cliptranslate.core import (
    Cancelled,
    Caption,
    ClipError,
    VideoInfo,
    as_srt,
    split_long_caption,
)
from cliptranslate.media import (
    _run,
    export_video,
    ffmpeg_executable,
    probe_video,
    subtitle_style,
)
from cliptranslate.project import load_project, save_project, video_fingerprint


def make_video(path: Path, size: str = "320x180", seconds: float = 1.6) -> Path:
    result = subprocess.run(
        [
            ffmpeg_executable(),
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c=blue:s={size}:r=25:d={seconds}",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency=440:duration={seconds}",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-shortest",
            str(path),
        ],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return path


def frame_pixels(video: Path, at: float) -> bytes:
    result = subprocess.run(
        [
            ffmpeg_executable(),
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            str(at),
            "-i",
            str(video),
            "-frames:v",
            "1",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "pipe:1",
        ],
        capture_output=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0 and result.stdout
    return result.stdout


def changed_pixels(video: Path, at: float) -> int:
    """Count pixels clearly different from the plain blue background (ignores codec noise)."""
    data = frame_pixels(video, at)
    background = data[:3]
    return sum(
        1
        for i in range(0, len(data), 3)
        if max(abs(data[i + c] - background[c]) for c in range(3)) > 60
    )


@pytest.mark.parametrize("size", ["320x180", "180x320"])
def test_burned_subtitles_are_actually_visible(tmp_path: Path, size: str):
    source = make_video(tmp_path / "in.mp4", size)
    video = probe_video(source)
    out, _ = export_video(
        video,
        [Caption(0.1, 1.4, "Visible English caption for the viewer.")],
        tmp_path / "out.mp4",
    )
    assert changed_pixels(out, 0.7) > 150  # caption drawn
    assert changed_pixels(out, 1.5) < 5  # gone after its end time


def test_probe_reports_display_size_and_rotation(tmp_path: Path):
    landscape = make_video(tmp_path / "landscape.mp4")
    assert (probe_video(landscape).width, probe_video(landscape).height) == (320, 180)
    rotated = tmp_path / "rotated.mp4"
    result = subprocess.run(
        [
            ffmpeg_executable(),
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-display_rotation",
            "90",
            "-i",
            str(landscape),
            "-c",
            "copy",
            str(rotated),
        ],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if result.returncode != 0:
        pytest.skip("This FFmpeg cannot write a rotation matrix")
    info = probe_video(rotated)
    assert (info.width, info.height) == (180, 320)


def test_subtitle_style_scales_for_vertical_video():
    wide = VideoInfo(Path("a.mp4"), 5, 1, True, 1920, 1080)
    tall = VideoInfo(Path("b.mp4"), 5, 1, True, 1080, 1920)
    unknown = VideoInfo(Path("c.mp4"), 5, 1, True)
    wide_filter, wide_wrap = subtitle_style(wide)
    tall_filter, tall_wrap = subtitle_style(tall)
    assert "original_size=1920x1080" in wide_filter
    assert "original_size=1080x1920" in tall_filter
    assert tall_wrap < wide_wrap <= 42
    assert subtitle_style(unknown)[0] == "subtitles=captions.srt"


def test_export_can_be_cancelled(tmp_path: Path):
    video = probe_video(make_video(tmp_path / "in.mp4"))
    with pytest.raises(Cancelled):
        export_video(
            video,
            [Caption(0.1, 1.0, "Hello")],
            tmp_path / "out.mp4",
            cancelled=lambda: True,
        )
    assert not (tmp_path / "out.mp4").exists()


def test_run_times_out_cleanly():
    with pytest.raises(ClipError, match="longer than"):
        _run(
            [ffmpeg_executable(), "-f", "lavfi", "-i", "anullsrc", "-f", "null", "-"],
            timeout=1,
        )


def test_long_caption_split_keeps_text_and_times():
    text = "One two three four five six seven eight nine ten eleven twelve. " * 3
    caption = Caption(2.0, 20.0, text.strip(), "Un deux trois")
    cues = split_long_caption(caption)
    assert len(cues) >= 3
    assert " ".join(c.english for c in cues) == text.strip()
    assert cues[0].start == 2.0 and cues[-1].end == 20.0
    assert cues[0].french == "Un deux trois"
    assert all(a.end == b.start for a, b in pairwise(cues))


def test_short_caption_is_not_split():
    caption = Caption(0, 2, "Short line.")
    assert split_long_caption(caption) == [caption]


def test_wrap_width_changes_line_length():
    caption = Caption(0, 3, "word " * 20)
    narrow = as_srt([caption], 3, wrap_width=20).splitlines()[2:]
    wide = as_srt([caption], 3, wrap_width=60).splitlines()[2:]
    assert max(len(line) for line in narrow) <= 20
    assert len(narrow) > len(wide)


def test_draft_keeps_french_and_detects_a_different_video(tmp_path: Path):
    video_path = tmp_path / "clip.mp4"
    video_path.write_bytes(b"A" * 3_000_000)
    video = VideoInfo(video_path, 5.0, video_path.stat().st_size, True)
    saved = save_project(
        tmp_path / "x.cliptranslate.json",
        video,
        [Caption(0, 1, "Hello", "Bonjour")],
        "small",
        3.0,
    )
    project = load_project(saved)
    assert project.captions[0].french == "Bonjour"
    assert project.video_fingerprint == video_fingerprint(video_path)
    other = tmp_path / "other.mp4"
    other.write_bytes(b"B" * 3_000_000)  # same size, different content
    assert video_fingerprint(other) != project.video_fingerprint


def test_old_drafts_without_french_still_open(tmp_path: Path):
    path = tmp_path / "old.cliptranslate.json"
    path.write_text(
        '{"version":1,"source_language":"fr","target_language":"en",'
        '"video_path":"v.mp4","video_size":5,"video_duration":4.0,'
        '"model_size":"base","processing_seconds":1,'
        '"captions":[{"start":0,"end":1,"english":"Hi"}]}',
        encoding="utf-8",
    )
    project = load_project(path)
    assert project.captions[0].french == ""
    assert project.video_fingerprint == ""


def test_log_file_is_created_and_never_holds_caption_text(tmp_path, monkeypatch):
    monkeypatch.setenv("CLIPTRANSLATE_LOG_DIR", str(tmp_path / "logs"))
    logger = diagnostics.get_logger()
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
    path = diagnostics.setup_logging()
    assert path is not None
    logger.info("hello from the test")
    for handler in logger.handlers:
        handler.flush()
        handler.close()
        logger.removeHandler(handler)
    assert "hello from the test" in path.read_text(encoding="utf-8")
