from itertools import pairwise
from pathlib import Path
from types import SimpleNamespace

import pytest

from cliptranslate import pipeline
from cliptranslate.core import Cancelled, ClipError, VideoInfo


def seg(start, end, text):
    return SimpleNamespace(start=start, end=end, text=text)


class FakeModel:
    """Answers the 'translate' and 'transcribe' tasks like faster-whisper does."""

    def __init__(self, english, french=()):
        self.english = english
        self.french = list(french)
        self.tasks = []

    def transcribe(self, audio_path, **kwargs):
        assert Path(audio_path).exists()
        assert kwargs["language"] == "fr"
        self.tasks.append(kwargs["task"])
        segments = self.english if kwargs["task"] == "translate" else self.french
        return iter(segments), None


@pytest.fixture
def no_model_download(monkeypatch):
    monkeypatch.setattr(
        pipeline,
        "extract_audio",
        lambda _video, path, **_kw: path.write_bytes(b"FAKE WAV"),
    )


def test_local_pipeline_generates_timed_english_captions(no_model_download):
    video = VideoInfo(Path("fake.mp4"), 3.0, 42, True)
    english = [
        seg(0.2, 1.5, "  Hello   there  "),
        seg(1.45, 2.6, "  How are you?  "),
    ]
    messages = []
    model = FakeModel(english)
    result = pipeline.translate_clip(
        video,
        with_french=False,
        progress=lambda percent, message: messages.append((percent, message)),
        model_factory=lambda size, cache: model,
    )
    assert [c.english for c in result.captions] == ["Hello there", "How are you?"]
    assert result.captions[1].start == result.captions[0].end
    assert model.tasks == ["translate"]
    assert messages[-1][0] == 100
    assert any(percent < 0 for percent, _ in messages)  # model-loading is indeterminate


def test_french_reference_is_attached_by_time(no_model_download):
    video = VideoInfo(Path("fake.mp4"), 4.0, 42, True)
    model = FakeModel(
        [seg(0.0, 1.5, "Hello there"), seg(1.5, 3.0, "How are you?")],
        [seg(0.1, 1.4, "Bonjour"), seg(1.6, 2.9, "Comment allez-vous ?")],
    )
    result = pipeline.translate_clip(video, model_factory=lambda *_: model)
    assert model.tasks == ["translate", "transcribe"]
    assert [c.french for c in result.captions] == ["Bonjour", "Comment allez-vous ?"]


def test_long_segments_are_split_into_readable_cues(no_model_download):
    video = VideoInfo(Path("fake.mp4"), 30.0, 42, True)
    text = (
        "This is a long first sentence that goes on for a while. "
        "Here is a second sentence, and then a third one follows right after it. "
        "Finally the speaker wraps everything up."
    )
    result = pipeline.translate_clip(
        video,
        with_french=False,
        model_factory=lambda *_: FakeModel([seg(0.0, 20.0, text)]),
    )
    assert len(result.captions) >= 3
    assert " ".join(c.english for c in result.captions) == text
    assert result.captions[0].start == 0.0
    assert result.captions[-1].end == 20.0
    for before, after in pairwise(result.captions):
        assert before.end == after.start
    assert all(c.end - c.start <= 7.5 for c in result.captions)


def test_cancel_stops_before_results(no_model_download):
    video = VideoInfo(Path("fake.mp4"), 3.0, 42, True)
    with pytest.raises(Cancelled):
        pipeline.translate_clip(
            video,
            cancelled=lambda: True,
            model_factory=lambda *_: FakeModel([seg(0, 1, "Hi")]),
        )


def test_empty_speech_is_an_actionable_error(no_model_download):
    with pytest.raises(ClipError, match="No usable subtitles"):
        pipeline.translate_clip(
            VideoInfo(Path("fake.mp4"), 2, 42, True),
            model_factory=lambda *_: FakeModel([]),
        )


def test_unknown_model_is_rejected_before_processing(no_model_download):
    with pytest.raises(ClipError, match="base or small"):
        pipeline.translate_clip(VideoInfo(Path("fake.mp4"), 2, 42, True), model_size="large")
