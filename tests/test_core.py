import pytest

from cliptranslate.core import (
    Caption,
    ClipError,
    as_srt,
    parse_timecode,
    timecode,
    validate_captions,
)


def test_timecodes_are_millisecond_precise():
    assert timecode(3601.256) == "01:00:01.256"
    assert timecode(0.9996, separator=",") == "00:00:01,000"
    assert parse_timecode("00:01:02,125") == 62.125
    assert parse_timecode("00:01:02.125") == 62.125
    with pytest.raises(ClipError, match="HH:MM:SS"):
        parse_timecode("99")


def test_srt_contains_unicode_and_sorted_timed_captions():
    captions = [
        Caption(0.125, 1.5, "Hello, world!"),
        Caption(1.5, 2.0, "It's summer.\nLet's go!"),
    ]
    result = as_srt(captions, 2.0)
    assert "1\n00:00:00,125 --> 00:00:01,500\nHello, world!" in result
    assert "2\n00:00:01,500 --> 00:00:02,000\nIt's summer.\nLet's go!" in result
    assert result.endswith("\n")


@pytest.mark.parametrize(
    "captions,reason",
    [
        ([], "no subtitles"),
        ([Caption(0, 1, " ")], "empty"),
        ([Caption(2, 1, "Hello")], "end after"),
        ([Caption(0, 2.2, "Hello")], "past the end"),
        ([Caption(0, 1, "One"), Caption(0.75, 2, "Two")], "overlaps"),
    ],
)
def test_rejects_unusable_subtitles(captions, reason):
    with pytest.raises(ClipError, match=reason):
        validate_captions(captions, 2.0)


def test_long_text_is_wrapped_without_changing_words():
    text = "This is a reasonably long sentence that needs to be wrapped to fit on a phone screen."
    result = as_srt([Caption(0, 4, text)], 4)
    lines = result.splitlines()[2:]
    assert all(len(line) <= 42 for line in lines)
    assert " ".join(lines) == text
