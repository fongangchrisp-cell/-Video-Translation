"""Domain objects and SRT formatting; no GUI or model dependencies."""

from __future__ import annotations

import math
import re
import textwrap
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

MAX_DURATION_SECONDS = 120
MAX_VIDEO_BYTES = 500 * 1024 * 1024
SUPPORTED_INPUTS = frozenset({".mp4", ".mov", ".mkv"})


class ClipError(Exception):
    """A recoverable error that should be shown to the user."""


class Cancelled(Exception):
    """The user stopped a running job. Not an error; nothing is saved or changed."""


@dataclass(frozen=True)
class VideoInfo:
    path: Path
    duration: float
    size: int
    has_audio: bool
    width: int = 0  # Displayed size after rotation; 0 when unknown.
    height: int = 0


@dataclass
class Caption:
    start: float
    end: float
    english: str
    french: str = ""  # Optional reference text so a reviewer can check the English.


_TIMECODE = re.compile(r"^(\d{2,}):([0-5]\d):([0-5]\d)[,.](\d{3})$")


def timecode(seconds: float, *, separator: str = ".") -> str:
    """Render a timestamp at millisecond precision (SRT uses a comma)."""
    if not math.isfinite(seconds) or seconds < 0:
        raise ClipError("Caption times must be non-negative numbers.")
    total_ms = round(seconds * 1000)
    hours, remaining = divmod(total_ms, 3_600_000)
    minutes, remaining = divmod(remaining, 60_000)
    whole_seconds, millis = divmod(remaining, 1000)
    return f"{hours:02d}:{minutes:02d}:{whole_seconds:02d}{separator}{millis:03d}"


def parse_timecode(value: str) -> float:
    """Accept 00:00:01.250 or 00:00:01,250 from the subtitle editor."""
    match = _TIMECODE.fullmatch(value.strip())
    if match is None:
        raise ClipError("Use the timestamp format HH:MM:SS.mmm (for example 00:00:03.500).")
    hours, minutes, seconds, millis = map(int, match.groups())
    return hours * 3600 + minutes * 60 + seconds + millis / 1000


def validate_captions(captions: Sequence[Caption], duration: float) -> None:
    if not captions:
        raise ClipError("There are no subtitles to save. Generate some first.")
    if not math.isfinite(duration) or duration <= 0:
        raise ClipError("The video duration is invalid.")
    previous_end = 0.0
    for index, caption in enumerate(captions, 1):
        if not math.isfinite(caption.start) or not math.isfinite(caption.end):
            raise ClipError(f"Subtitle {index} has an invalid timestamp.")
        if caption.start < 0 or caption.end <= caption.start:
            raise ClipError(
                f"Subtitle {index} must end after it starts, and start at or after zero."
            )
        # Container metadata can round a few milliseconds differently from speech timestamps.
        if caption.end > duration + 0.05:
            raise ClipError(f"Subtitle {index} extends past the end of the video.")
        if index > 1 and caption.start < previous_end - 0.001:
            raise ClipError(
                f"Subtitle {index} overlaps the previous subtitle. Adjust its start time."
            )
        if not caption.english.strip():
            raise ClipError(f"Subtitle {index} is empty. Edit or delete that row.")
        previous_end = caption.end


DEFAULT_WRAP_WIDTH = 42
MAX_CAPTION_SECONDS = 6.0
MAX_CAPTION_CHARS = 84


def _wrap_subtitle(text: str, width: int = DEFAULT_WRAP_WIDTH) -> str:
    """Wrap for small screens while respecting line breaks deliberately added by an editor."""
    lines = []
    for paragraph in text.strip().splitlines():
        normalized = " ".join(paragraph.split())
        lines.extend(
            textwrap.wrap(normalized, width=width, break_long_words=False, break_on_hyphens=False)
            or [""]
        )
    return "\n".join(lines)


def as_srt(
    captions: Sequence[Caption],
    duration: float,
    *,
    wrap_width: int = DEFAULT_WRAP_WIDTH,
) -> str:
    validate_captions(captions, duration)
    blocks = []
    for index, caption in enumerate(captions, 1):
        blocks.append(
            f"{index}\n"
            f"{timecode(caption.start, separator=',')} --> {timecode(caption.end, separator=',')}\n"
            f"{_wrap_subtitle(caption.english, wrap_width)}"
        )
    return "\n\n".join(blocks) + "\n"


def _chunk_words(words: list[str], parts: int) -> list[list[str]]:
    """Split words into ``parts`` groups of similar length, preferring sentence/comma breaks."""
    total = sum(len(word) + 1 for word in words)
    groups: list[list[str]] = []
    current: list[str] = []
    used = 0
    for index, word in enumerate(words):
        current.append(word)
        used += len(word) + 1
        remaining_parts = parts - len(groups) - 1
        if remaining_parts <= 0:
            continue
        target = total * (len(groups) + 1) / parts
        words_left = len(words) - index - 1
        at_punctuation = used >= target * 0.75 and word[-1:] in ".!?;:,"
        break_here = words_left < remaining_parts or at_punctuation or used >= target * 1.1
        if break_here and words_left >= remaining_parts:
            groups.append(current)
            current = []
    if current:
        groups.append(current)
    return groups


def split_long_caption(
    caption: Caption,
    *,
    max_seconds: float = MAX_CAPTION_SECONDS,
    max_chars: int = MAX_CAPTION_CHARS,
) -> list[Caption]:
    """Break a long speech segment into readable cues; times follow text length.

    The French reference text is kept on the first cue only when the segment is split,
    because it cannot be divided reliably. The editor shows it for the whole group.
    """
    words = caption.english.split()
    duration = caption.end - caption.start
    parts = max(
        math.ceil(duration / max_seconds),
        math.ceil(len(caption.english) / max_chars),
        1,
    )
    parts = min(parts, len(words)) if words else 1
    if parts <= 1:
        return [caption]
    groups = _chunk_words(words, parts)
    if len(groups) <= 1:
        return [caption]
    lengths = [sum(len(word) + 1 for word in group) for group in groups]
    total = sum(lengths)
    cues: list[Caption] = []
    cursor = caption.start
    consumed = 0
    for index, (group, length) in enumerate(zip(groups, lengths, strict=True)):
        consumed += length
        end = (
            caption.end
            if index == len(groups) - 1
            else round(caption.start + duration * consumed / total, 3)
        )
        cues.append(
            Caption(
                start=round(cursor, 3),
                end=end,
                english=" ".join(group),
                french=caption.french if index == 0 else "",
            )
        )
        cursor = end
    return [cue for cue in cues if cue.end > cue.start]
