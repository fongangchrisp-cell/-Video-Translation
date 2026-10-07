"""The local French-speech-to-English-caption pipeline."""

from __future__ import annotations

import math
import os
import sys
import tempfile
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

from .core import Cancelled, Caption, ClipError, VideoInfo, split_long_caption
from .media import extract_audio

MODEL_SIZES = ("base", "small")
# A percent below zero means "working, but progress cannot be measured" (model download).
Progress = Callable[[int, str], None]
CancelCheck = Callable[[], bool]


@dataclass(frozen=True)
class ProcessingResult:
    captions: list[Caption]
    elapsed_seconds: float


def cache_dir() -> Path:
    """Keep downloaded model weights outside both the project and creator videos."""
    override = os.environ.get("CLIPTRANSLATE_CACHE_DIR")
    if override:
        return Path(override).expanduser().resolve()
    if sys.platform == "win32":
        return Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "ClipTranslate" / "models"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Caches" / "ClipTranslate" / "models"
    return Path.home() / ".cache" / "cliptranslate" / "models"


def _model(size: str, cache: Path):
    try:
        from faster_whisper import WhisperModel

        cache.mkdir(parents=True, exist_ok=True)
        return WhisperModel(size, device="cpu", compute_type="int8", download_root=str(cache))
    except Exception as exc:
        raise ClipError(
            "Could not load the speech model. The first run needs an internet connection "
            "to download it; later runs use the local cache. Check available disk space "
            f"and try again. Details: {str(exc)[:250]}"
        ) from exc


def _segments(
    segments: Iterable[object],
    duration: float,
    cancelled: CancelCheck,
    on_segment: Callable[[int, float], None],
) -> list[tuple[float, float, str]]:
    """Collect clean (start, end, text) tuples; faster-whisper yields lazily."""
    found: list[tuple[float, float, str]] = []
    for segment in segments:
        if cancelled():
            raise Cancelled("Cancelled.")
        start, end = float(segment.start), float(segment.end)  # type: ignore[attr-defined]
        if math.isfinite(start) and math.isfinite(end):
            text = " ".join(str(segment.text).split())  # type: ignore[attr-defined]
            end = min(duration, end)
            if text and end > start + 0.01:
                found.append((max(0.0, start), end, text))
        on_segment(len(found), max(0.0, end if math.isfinite(end) else 0.0))
    return found


def attach_french(captions: list[Caption], french: list[tuple[float, float, str]]) -> None:
    """Give each caption the French lines spoken during it (midpoint rule)."""
    for caption in captions:
        parts = [
            text for start, end, text in french if caption.start <= (start + end) / 2 < caption.end
        ]
        caption.french = " ".join(parts)


def translate_clip(
    video: VideoInfo,
    *,
    model_size: str = "small",
    with_french: bool = True,
    progress: Progress | None = None,
    cancelled: CancelCheck | None = None,
    model_factory: Callable[[str, Path], object] | None = None,
) -> ProcessingResult:
    """Extract the first audio track, translate it to English, and (optionally) also
    transcribe the French so a reviewer can check the English against what was said.

    This intentionally supports only French speech -> English text. It does not send
    video/audio to a hosted API. ``model_factory`` is injectable for offline tests.
    """
    if model_size not in MODEL_SIZES:
        raise ClipError("Select the base or small speech model.")
    if not math.isfinite(video.duration) or video.duration <= 0:
        raise ClipError("This video has an invalid duration.")
    report = progress or (lambda _percent, _message: None)
    stop = cancelled or (lambda: False)
    started = time.monotonic()
    translate_end = 60 if with_french else 95
    with tempfile.TemporaryDirectory(prefix="cliptranslate-audio-") as folder:
        audio_path = Path(folder) / "speech.wav"
        report(5, "Extracting the first audio track…")
        extract_audio(video, audio_path, cancelled=stop)
        report(
            -1,
            "Loading the speech model. The first run downloads it and can take minutes…",
        )
        model = (model_factory or _model)(model_size, cache_dir())
        if stop():
            raise Cancelled("Cancelled.")
        report(18, "Listening to French speech and translating to English…")
        try:
            segments, _info = model.transcribe(  # type: ignore[attr-defined]
                str(audio_path),
                language="fr",
                task="translate",
                beam_size=5,
                vad_filter=True,
            )

            def english_progress(count: int, position: float) -> None:
                share = min(1.0, position / video.duration)
                report(
                    min(translate_end, 18 + int((translate_end - 18) * share)),
                    f"Translating speech… {count} segments found",
                )

            english = _segments(segments, video.duration, stop, english_progress)
            french: list[tuple[float, float, str]] = []
            if with_french and english:
                report(60, "Transcribing the French original for your review…")
                french_segments, _ = model.transcribe(  # type: ignore[attr-defined]
                    str(audio_path),
                    language="fr",
                    task="transcribe",
                    beam_size=5,
                    vad_filter=True,
                )

                def french_progress(count: int, position: float) -> None:
                    share = min(1.0, position / video.duration)
                    report(60 + int(35 * share), f"Transcribing French… {count} lines")

                french = _segments(french_segments, video.duration, stop, french_progress)
        except (ClipError, Cancelled):
            raise
        except Exception as exc:
            raise ClipError(f"Speech translation failed: {str(exc)[:300]}") from exc

    captions: list[Caption] = []
    previous_end = 0.0
    for start, end, text in english:
        start = max(start, previous_end)
        if end <= start + 0.01:
            continue
        captions.extend(split_long_caption(Caption(round(start, 3), round(end, 3), text)))
        previous_end = end
    if not captions:
        raise ClipError("No usable subtitles were produced. Try a clip with clear French dialogue.")
    if french:
        attach_french(captions, french)
    report(100, "Subtitles ready. Review and correct them before sharing.")
    return ProcessingResult(captions=captions, elapsed_seconds=time.monotonic() - started)
