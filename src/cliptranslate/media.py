"""Safe local FFmpeg invocation for probing, audio extraction and video export."""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
import time
from collections.abc import Callable, Sequence
from pathlib import Path

import imageio_ffmpeg

from .core import (
    DEFAULT_WRAP_WIDTH,
    MAX_DURATION_SECONDS,
    MAX_VIDEO_BYTES,
    SUPPORTED_INPUTS,
    Cancelled,
    Caption,
    ClipError,
    VideoInfo,
    as_srt,
)

_DURATION = re.compile(r"Duration:\s*(\d+):([0-5]\d):([0-5]\d(?:\.\d+)?)")
_VIDEO_LINE = re.compile(r"Stream #.*Video:.*?[\s,](\d{2,5})x(\d{2,5})")
_ROTATION = re.compile(r"rotation of (-?\d+(?:\.\d+)?) degrees")
CancelCheck = Callable[[], bool]
_SRT_GRID_WIDTH = 384
_SRT_GRID_HEIGHT = 288


def ffmpeg_executable() -> str:
    """Allow an external FFmpeg override; otherwise use the packaged binary."""
    override = os.environ.get("CLIPTRANSLATE_FFMPEG")
    if override:
        if not Path(override).is_file():
            raise ClipError("CLIPTRANSLATE_FFMPEG does not point to an FFmpeg executable.")
        return override
    try:
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as exc:
        raise ClipError(
            "FFmpeg is unavailable. Reinstall imageio-ffmpeg or set CLIPTRANSLATE_FFMPEG."
        ) from exc


def _run(
    args: list[str],
    *,
    cwd: Path | None = None,
    timeout: int = 180,
    cancelled: CancelCheck | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run FFmpeg, polling ``cancelled`` so a long job can be stopped by the user."""
    try:
        process = subprocess.Popen(
            args,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            errors="replace",
        )
    except OSError as exc:
        raise ClipError(f"FFmpeg could not start: {exc}") from exc
    deadline = time.monotonic() + timeout
    while True:
        if cancelled is not None and cancelled():
            process.kill()
            process.communicate()
            raise Cancelled("Cancelled.")
        try:
            stdout, stderr = process.communicate(timeout=0.25)
            return subprocess.CompletedProcess(args, process.returncode, stdout, stderr)
        except subprocess.TimeoutExpired:
            if time.monotonic() > deadline:
                process.kill()
                process.communicate()
                raise ClipError(
                    f"FFmpeg took longer than {timeout} seconds and was stopped."
                ) from None


def probe_video(path: Path) -> VideoInfo:
    path = Path(path).expanduser().resolve()
    if not path.is_file():
        raise ClipError("Choose a video file that exists on this computer.")
    if path.suffix.lower() not in SUPPORTED_INPUTS:
        raise ClipError("Choose an MP4, MOV or MKV video for this pilot.")
    size = path.stat().st_size
    if size == 0 or size > MAX_VIDEO_BYTES:
        raise ClipError("The video must be non-empty and at most 500 MiB.")

    result = _run([ffmpeg_executable(), "-hide_banner", "-nostdin", "-i", str(path)], timeout=20)
    metadata = result.stderr
    match = _DURATION.search(metadata)
    if match is None or "Video:" not in metadata:
        raise ClipError(
            "Could not read a video stream and duration from this file. Try another clip."
        )
    hours, minutes, seconds = match.groups()
    duration = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    if duration <= 0 or duration > MAX_DURATION_SECONDS:
        raise ClipError(f"This pilot accepts videos up to {MAX_DURATION_SECONDS} seconds long.")
    has_audio = "Audio:" in metadata
    if not has_audio:
        raise ClipError("This video has no audio track to translate.")
    width = height = 0
    size_match = _VIDEO_LINE.search(metadata)
    if size_match is not None:
        width, height = int(size_match.group(1)), int(size_match.group(2))
        rotation = _ROTATION.search(metadata)
        if rotation is not None and round(abs(float(rotation.group(1)))) % 180 == 90:
            width, height = height, width  # FFmpeg auto-rotates phone footage.
    return VideoInfo(
        path=path,
        duration=duration,
        size=size,
        has_audio=has_audio,
        width=width,
        height=height,
    )


def extract_audio(
    video: VideoInfo, destination: Path, *, cancelled: CancelCheck | None = None
) -> None:
    """Decode the first audio track to mono 16 kHz WAV for speech recognition."""
    result = _run(
        [
            ffmpeg_executable(),
            "-hide_banner",
            "-nostdin",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(video.path),
            "-map",
            "0:a:0",
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-c:a",
            "pcm_s16le",
            str(destination),
        ],
        timeout=180,
        cancelled=cancelled,
    )
    if result.returncode != 0 or not destination.is_file() or destination.stat().st_size == 0:
        raise ClipError(f"Could not extract the first audio track. {result.stderr[-600:].strip()}")


def save_srt(captions: Sequence[Caption], duration: float, output: Path) -> Path:
    """Write UTF-8 SRT atomically so a failed save does not destroy the previous export."""
    output = Path(output).expanduser().resolve()
    if output.suffix.lower() != ".srt":
        raise ClipError("Choose a filename ending in .srt.")
    content = as_srt(captions, duration)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=output.parent,
            prefix=".cliptranslate-",
            suffix=".srt",
            delete=False,
        ) as file:
            temporary = Path(file.name)
            file.write(content)
        os.replace(temporary, output)
    except OSError as exc:
        raise ClipError(f"Could not save subtitles: {exc}") from exc
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return output


def subtitle_style(video: VideoInfo) -> tuple[str, int]:
    """Return a libass filter and the wrap width for this video's real shape.

    Sizing is relative to the picture so captions are readable on 16:9 clips and on
    vertical (9:16) phone clips, where the default style would run off the screen.
    """
    width, height = video.width, video.height
    if width <= 0 or height <= 0:
        return "subtitles=captions.srt", DEFAULT_WRAP_WIDTH
    # libass sizes SRT text in a 384x288 script grid, not in pixels, so convert.
    font_px = max(14, round(min(width, height) * 0.045))
    font_units = font_px * _SRT_GRID_HEIGHT / height
    margin_v = round(0.06 * _SRT_GRID_HEIGHT)
    margin_h = round(0.06 * _SRT_GRID_WIDTH)
    usable_px = width * 0.88
    wrap = max(16, min(DEFAULT_WRAP_WIDTH, int(usable_px / (font_px * 0.6))))
    style = (
        f"FontSize={font_units:.1f},Outline=1.5,Shadow=0,MarginV={margin_v},"
        f"MarginL={margin_h},MarginR={margin_h},Bold=1"
    )
    return (
        f"subtitles=captions.srt:original_size={width}x{height}:force_style='{style}'",
        wrap,
    )


def export_video(
    video: VideoInfo,
    captions: Sequence[Caption],
    output: Path,
    *,
    cancelled: CancelCheck | None = None,
) -> tuple[Path, Path]:
    """Burn edited subtitles into a shareable MP4; also save a matching editable SRT."""
    output = Path(output).expanduser().resolve()
    if output.suffix.lower() != ".mp4":
        raise ClipError("Choose a filename ending in .mp4.")
    if output == video.path:
        raise ClipError("Choose an output filename different from the original video.")
    video_filter, wrap_width = subtitle_style(video)
    # Also validates every caption before any work begins.
    content = as_srt(captions, video.duration, wrap_width=wrap_width)
    filter_list = _run([ffmpeg_executable(), "-hide_banner", "-filters"], timeout=20)
    if filter_list.returncode != 0 or not re.search(r"\s+subtitles\s+V->V\s", filter_list.stdout):
        raise ClipError(
            "This FFmpeg build lacks the subtitles/libass filter. Save the SRT or use a full FFmpeg build."
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".cliptranslate-", dir=output.parent) as folder:
        staging = Path(folder)
        (staging / "captions.srt").write_text(content, encoding="utf-8")
        temporary_video = staging / "render.mp4"
        # The filter reads a fixed, simple filename in cwd. This avoids FFmpeg filtergraph
        # escaping issues with user-selected paths containing spaces, colons or apostrophes.
        result = _run(
            [
                ffmpeg_executable(),
                "-hide_banner",
                "-nostdin",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(video.path),
                "-map",
                "0:v:0",
                "-map",
                "0:a:0",
                "-vf",
                video_filter,
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "23",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-b:a",
                "160k",
                "-sn",
                "-movflags",
                "+faststart",
                str(temporary_video),
            ],
            cwd=staging,
            timeout=1800,
            cancelled=cancelled,
        )
        if (
            result.returncode != 0
            or not temporary_video.is_file()
            or temporary_video.stat().st_size == 0
        ):
            raise ClipError(f"Could not render the subtitled video. {result.stderr[-900:].strip()}")
        try:
            os.replace(temporary_video, output)
        except OSError as exc:
            raise ClipError(f"Could not save the rendered video: {exc}") from exc
    srt_path = output.with_suffix(".srt")
    save_srt(captions, video.duration, srt_path)  # Standard width for other players.
    return output, srt_path
