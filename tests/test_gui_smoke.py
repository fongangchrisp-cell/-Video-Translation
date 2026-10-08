"""Headless checks of the editor. Skipped where Qt cannot load (e.g. minimal containers)."""

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
widgets = pytest.importorskip("PySide6.QtWidgets", exc_type=ImportError)
pytest.importorskip("PySide6.QtMultimedia", exc_type=ImportError)

from cliptranslate import gui
from cliptranslate.core import Cancelled, Caption, VideoInfo


@pytest.fixture(scope="module")
def app():
    return widgets.QApplication.instance() or widgets.QApplication([])


@pytest.fixture
def window(app):
    win = gui.MainWindow()
    win.video = VideoInfo(Path("clip.mp4"), 20.0, 10, True, 640, 360)
    win.rights.setChecked(True)
    win._set_captions(
        [
            Caption(0.0, 2.0, "Hello there", "Bonjour"),
            Caption(2.0, 4.0, "How are you", "Comment allez-vous"),
        ]
    )
    win.dirty = False
    yield win
    win.dirty = False
    win.close()


def choose(monkeypatch, label):
    """Make the next QMessageBox behave as if the user clicked the named button."""

    def clicked(self):
        return next(b for b in self.buttons() if b.text() == label)

    monkeypatch.setattr(widgets.QMessageBox, "clickedButton", clicked)


def test_french_reference_is_shown_and_survives_edits(window):
    assert "Bonjour" in window.french_label.text()
    window.table.setCurrentCell(1, 3)
    assert "Comment allez-vous" in window.french_label.text()
    window.table.setCurrentCell(0, 3)
    window.merge_next()
    assert window.table.rowCount() == 1
    captions = window._captions_from_table()
    assert captions[0].french == "Bonjour Comment allez-vous"
    assert captions[0].english == "Hello there How are you"
    window.split_line()
    assert window.table.rowCount() == 2
    assert window._captions_from_table()[0].french == "Bonjour Comment allez-vous"


def test_edits_mark_the_project_unsaved(window):
    assert not window.dirty
    window.english_edit.setPlainText("Hello again")
    assert window.dirty


def test_closing_with_unsaved_edits_can_be_cancelled(window, monkeypatch):
    window.english_edit.setPlainText("Changed")
    monkeypatch.setattr(widgets.QMessageBox, "exec", lambda self: 0)
    choose(monkeypatch, "Keep editing")
    assert window.close() is False


def test_closing_discards_when_user_chooses(window, monkeypatch):
    window.english_edit.setPlainText("Changed")
    monkeypatch.setattr(widgets.QMessageBox, "exec", lambda self: 0)
    choose(monkeypatch, "Discard")
    assert window.close() is True


def test_unmeasurable_progress_is_indeterminate(window):
    window._progress_changed(-1, "Loading the speech model…")
    assert (window.progress.minimum(), window.progress.maximum()) == (0, 0)
    window._progress_changed(40, "Translating…")
    assert window.progress.maximum() == 100 and window.progress.value() == 40


def test_cancel_button_only_shows_while_busy(window):
    window._refresh_buttons()
    assert window.cancel_button.isHidden()
    window.busy = True
    window._refresh_buttons()
    assert not window.cancel_button.isHidden()
    window.busy = False
    window._refresh_buttons()


def test_translate_worker_reports_cancellation(app, monkeypatch):
    def fake_translate(video, **kwargs):
        assert kwargs["cancelled"]()
        raise Cancelled("Cancelled.")

    monkeypatch.setattr(gui, "translate_clip", fake_translate)
    holder = widgets.QWidget()
    worker = gui.TranslateWorker(VideoInfo(Path("clip.mp4"), 5.0, 1, True), "base", True, holder)
    seen = []
    worker.cancelled.connect(lambda: seen.append("cancelled"))
    worker.failed.connect(lambda message: seen.append(message))
    worker.request_cancel()
    worker.run()
    assert seen == ["cancelled"]


def test_demo_mode_loads_without_a_model(app):
    win = gui.MainWindow()
    win.load_demo()
    assert win.table.rowCount() == 6
    assert win.video is not None and win.rights.isChecked()
    assert "Bonjour" in win.french_label.text()
    assert "DEMO" in win.windowTitle()
    assert not win.dirty
    win.close()
