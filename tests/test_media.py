import subprocess
from pathlib import Path

import pytest

from cliptranslate.core import Caption, ClipError
from cliptranslate.media import (
    export_video,
    extract_audio,
    ffmpeg_executable,
    probe_video,
    save_srt,
)


@pytest.fixture
def short_video(tmp_path: Path) -> Path:
    path = tmp_path / "creator's clip (FR).mp4"
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
            "color=c=blue:s=320x180:r=25:d=1.6",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:duration=1.6",
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


def test_probe_and_extract_audio(short_video: Path, tmp_path: Path):
    video = probe_video(short_video)
    assert 1.5 <= video.duration <= 1.7
    assert video.has_audio
    audio = tmp_path / "speech.wav"
    extract_audio(video, audio)
    assert audio.stat().st_size > 10000


def test_export_renders_subtitles_even_when_paths_have_quotes(short_video: Path, tmp_path: Path):
    video = probe_video(short_video)
    captions = [Caption(0.1, 1.3, "This is an English caption.")]
    destination = tmp_path / "creator's English output.mp4"
    mp4, srt = export_video(video, captions, destination)
    assert mp4 == destination
    assert mp4.stat().st_size > 1000
    assert srt.read_text(encoding="utf-8").startswith("1\n00:00:00,100 --> 00:00:01,300")
    assert 1.5 <= probe_video(mp4).duration <= 1.7


def test_srt_save_and_unsupported_input(tmp_path: Path):
    path = tmp_path / "english.srt"
    save_srt([Caption(0, 1, "Hello")], 1, path)
    assert path.read_text(encoding="utf-8").endswith("Hello\n")
    other = tmp_path / "audio.mp3"
    other.write_bytes(b"not a video")
    with pytest.raises(ClipError, match="MP4, MOV or MKV"):
        probe_video(other)


def test_bad_captions_do_not_replace_an_existing_export(short_video: Path, tmp_path: Path):
    existing = tmp_path / "previous.mp4"
    existing.write_bytes(b"Keep the previous output")
    with pytest.raises(ClipError, match="past the end"):
        export_video(probe_video(short_video), [Caption(0, 99, "Too long")], existing)
    assert existing.read_bytes() == b"Keep the previous output"


def test_silent_video_is_rejected(tmp_path: Path):
    path = tmp_path / "silent.mp4"
    subprocess.run(
        [
            ffmpeg_executable(),
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=red:s=160x90:r=25:d=0.5",
            "-c:v",
            "libx264",
            str(path),
        ],
        capture_output=True,
        text=True,
        timeout=60,
        check=True,
    )
    with pytest.raises(ClipError, match="no audio track"):
        probe_video(path)
