"""Native desktop interface for the ten-creator French-to-English pilot."""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

from PySide6.QtCore import Qt, QThread, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QScrollArea,
    QPushButton,
    QSlider,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .core import (
    Cancelled,
    Caption,
    ClipError,
    VideoInfo,
    parse_timecode,
    timecode,
    validate_captions,
)
from .demo import create_demo_clip, demo_captions
from .diagnostics import get_logger, log_dir, setup_logging
from .media import export_video, probe_video, save_srt
from .pipeline import ProcessingResult, translate_clip
from .project import load_project, save_project, video_fingerprint

log = get_logger()
FRENCH_ROLE = Qt.ItemDataRole.UserRole + 1


class TranslateWorker(QThread):
    updated = Signal(int, str)
    succeeded = Signal(object)
    failed = Signal(str)
    cancelled = Signal()

    def __init__(self, video: VideoInfo, model_size: str, with_french: bool, parent: QWidget):
        super().__init__(parent)
        self.video = video
        self.model_size = model_size
        self.with_french = with_french
        self.stop_requested = False

    def request_cancel(self) -> None:
        self.stop_requested = True

    def run(self) -> None:
        try:
            result = translate_clip(
                self.video,
                model_size=self.model_size,
                with_french=self.with_french,
                progress=self.updated.emit,
                cancelled=lambda: self.stop_requested,
            )
            log.info(
                "translated %s: %d cues in %.0fs (model=%s, french=%s)",
                self.video.path.name,
                len(result.captions),
                result.elapsed_seconds,
                self.model_size,
                self.with_french,
            )
            self.succeeded.emit(result)
        except Cancelled:
            log.info("translation cancelled for %s", self.video.path.name)
            self.cancelled.emit()
        except ClipError as exc:
            log.warning("translation failed for %s: %s", self.video.path.name, exc)
            self.failed.emit(str(exc))
        except Exception as exc:
            log.exception("unexpected translation error")
            self.failed.emit(
                f"Unexpected processing error: {exc}\n\nDetails were saved to the log file."
            )


class ExportWorker(QThread):
    succeeded = Signal(object)
    failed = Signal(str)
    cancelled = Signal()

    def __init__(
        self,
        video: VideoInfo,
        captions: list[Caption],
        destination: Path,
        parent: QWidget,
    ):
        super().__init__(parent)
        self.video = video
        self.captions = captions
        self.destination = destination
        self.stop_requested = False

    def request_cancel(self) -> None:
        self.stop_requested = True

    def run(self) -> None:
        try:
            files = export_video(
                self.video,
                self.captions,
                self.destination,
                cancelled=lambda: self.stop_requested,
            )
            log.info("exported %s", self.destination.name)
            self.succeeded.emit(files)
        except Cancelled:
            log.info("export cancelled for %s", self.destination.name)
            self.cancelled.emit()
        except ClipError as exc:
            log.warning("export failed for %s: %s", self.destination.name, exc)
            self.failed.emit(str(exc))
        except Exception as exc:
            log.exception("unexpected export error")
            self.failed.emit(
                f"Unexpected export error: {exc}\n\nDetails were saved to the log file."
            )


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("ClipTranslate  •  French → English")
        screen = QApplication.primaryScreen()
        available = screen.availableGeometry().height() - 60 if screen else 860
        self.resize(1180, max(560, min(860, available)))
        self.setMinimumWidth(930)  # Height follows the layout so nothing overlaps.
        self.video: VideoInfo | None = None
        self.project_path: Path | None = None
        self.processing_seconds = 0.0
        self.worker: TranslateWorker | ExportWorker | None = None
        self.busy = False
        self.dirty = False
        self.active_row = -1
        self._syncing = False
        self._notice_shown = False
        self._build_ui()
        self._refresh_buttons()

    def _build_ui(self) -> None:
        root = QWidget()
        outer = QVBoxLayout(root)
        outer.setContentsMargins(22, 20, 22, 20)
        outer.setSpacing(14)
        # Scroll on small screens instead of squeezing or overlapping controls.
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(root)
        self.setCentralWidget(scroll)

        header = QFrame()
        header.setObjectName("header")
        header_row = QHBoxLayout(header)
        header_row.setContentsMargins(20, 14, 20, 14)
        title_box = QVBoxLayout()
        eyebrow = QLabel("CREATOR PILOT  /  DESKTOP")
        eyebrow.setObjectName("eyebrow")
        title_box.addWidget(eyebrow)
        title = QLabel("ClipTranslate")
        title.setObjectName("title")
        title_box.addWidget(title)
        subtitle = QLabel(
            "Short French videos → editable English subtitles. No lip-sync, no cloud upload."
        )
        subtitle.setObjectName("muted")
        title_box.addWidget(subtitle)
        header_row.addLayout(title_box, 1)
        badge = QLabel("FR  →  EN     •     LOCAL")
        badge.setObjectName("badge")
        header_row.addWidget(badge)
        outer.addWidget(header)

        setup = QFrame()
        setup.setObjectName("card")
        setup_layout = QVBoxLayout(setup)
        setup_layout.setContentsMargins(18, 14, 18, 14)
        setup_layout.setSpacing(10)
        file_row = QHBoxLayout()
        self.file_label = QLabel("No video selected · MP4, MOV or MKV · up to 2 minutes / 500 MiB")
        self.file_label.setTextFormat(Qt.TextFormat.PlainText)
        self.file_label.setObjectName("file")
        self.file_label.setWordWrap(True)
        file_row.addWidget(self.file_label, 1)
        self.choose_button = QPushButton("Choose video")
        self.choose_button.clicked.connect(self.choose_video)
        file_row.addWidget(self.choose_button)
        setup_layout.addLayout(file_row)
        controls = QHBoxLayout()
        controls.addWidget(QLabel("Speech model"))
        self.model_select = QComboBox()
        self.model_select.addItem("Base · faster", "base")
        self.model_select.addItem("Small · better quality", "small")
        self.model_select.setCurrentIndex(1)
        self.model_select.setToolTip(
            "Both run locally on the CPU. Small takes longer and downloads more data."
        )
        controls.addWidget(self.model_select)
        self.french_check = QCheckBox("Also transcribe the French (slower, lets you check)")
        self.french_check.setChecked(True)
        self.french_check.setToolTip(
            "Shows the French that was recognised beside each English line, so a "
            "reviewer can catch mistranslations. Adds roughly the same processing time again."
        )
        controls.addWidget(self.french_check)
        controls.addStretch(1)
        self.log_button = QPushButton("Open log folder")
        self.log_button.setToolTip("Send the log file to the team if something goes wrong.")
        self.log_button.clicked.connect(self.open_logs)
        controls.addWidget(self.log_button)
        self.cancel_button = QPushButton("Cancel job")
        self.cancel_button.clicked.connect(self.cancel_job)
        self.cancel_button.setVisible(False)
        controls.addWidget(self.cancel_button)
        self.generate_button = QPushButton("Generate English subtitles")
        self.generate_button.setObjectName("primary")
        self.generate_button.clicked.connect(self.generate_subtitles)
        controls.addWidget(self.generate_button)
        setup_layout.addLayout(controls)
        self.rights = QCheckBox("I have permission to process and share this video.")
        self.rights.toggled.connect(self._refresh_buttons)
        setup_layout.addWidget(self.rights)
        self.progress_label = QLabel(
            "Choose your own video to begin. First use downloads the speech model once."
        )
        self.progress_label.setObjectName("muted")
        setup_layout.addWidget(self.progress_label)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setMaximumHeight(6)
        setup_layout.addWidget(self.progress)
        outer.addWidget(setup)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        captions_card = QFrame()
        captions_card.setObjectName("card")
        captions_layout = QVBoxLayout(captions_card)
        captions_layout.setContentsMargins(16, 14, 16, 14)
        caption_head = QHBoxLayout()
        left_title = QLabel("Subtitles")
        left_title.setObjectName("sectionTitle")
        caption_head.addWidget(left_title)
        caption_head.addStretch(1)
        self.caption_count = QLabel("0 lines")
        self.caption_count.setObjectName("muted")
        caption_head.addWidget(self.caption_count)
        captions_layout.addLayout(caption_head)
        hint = QLabel(
            "Select a row to preview it. Edit its text and timestamps below, or double-click a cell."
        )
        hint.setObjectName("muted")
        hint.setWordWrap(True)
        captions_layout.addWidget(hint)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["#", "START", "END", "ENGLISH SUBTITLE"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.EditKeyPressed
        )
        self.table.setAlternatingRowColors(True)
        self.table.setWordWrap(True)
        self.table.verticalHeader().setVisible(False)
        columns = self.table.horizontalHeader()
        columns.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        columns.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        columns.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        columns.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(1, 115)
        self.table.setColumnWidth(2, 115)
        self.table.currentCellChanged.connect(self._row_changed)
        self.table.itemChanged.connect(self._item_changed)
        self.table.setMinimumHeight(150)
        captions_layout.addWidget(self.table, 1)

        edit_label = QLabel("EDIT SELECTED LINE")
        edit_label.setObjectName("eyebrow")
        captions_layout.addWidget(edit_label)
        self.english_edit = QPlainTextEdit()
        self.english_edit.setPlaceholderText("English subtitle text…")
        self.english_edit.setFixedHeight(64)
        self.english_edit.textChanged.connect(self._editor_changed)
        captions_layout.addWidget(self.english_edit)
        self.french_label = QLabel("")
        self.french_label.setObjectName("muted")
        self.french_label.setTextFormat(Qt.TextFormat.PlainText)
        self.french_label.setWordWrap(True)
        self.french_label.setMinimumHeight(22)
        captions_layout.addWidget(self.french_label)
        time_row = QHBoxLayout()
        time_row.addWidget(QLabel("Start"))
        self.start_edit = QLineEdit()
        self.start_edit.setPlaceholderText("00:00:00.000")
        self.start_edit.textEdited.connect(self._editor_changed)
        time_row.addWidget(self.start_edit)
        time_row.addWidget(QLabel("End"))
        self.end_edit = QLineEdit()
        self.end_edit.setPlaceholderText("00:00:00.000")
        self.end_edit.textEdited.connect(self._editor_changed)
        time_row.addWidget(self.end_edit)
        captions_layout.addLayout(time_row)
        edit_buttons = QHBoxLayout()
        self.add_button = QPushButton("Add line")
        self.add_button.clicked.connect(self.add_line)
        edit_buttons.addWidget(self.add_button)
        self.split_button = QPushButton("Split line")
        self.split_button.clicked.connect(self.split_line)
        edit_buttons.addWidget(self.split_button)
        self.merge_button = QPushButton("Merge next")
        self.merge_button.clicked.connect(self.merge_next)
        edit_buttons.addWidget(self.merge_button)
        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_line)
        edit_buttons.addWidget(self.delete_button)
        edit_buttons.addStretch(1)
        captions_layout.addLayout(edit_buttons)
        splitter.addWidget(captions_card)

        preview_card = QFrame()
        preview_card.setObjectName("card")
        preview_layout = QVBoxLayout(preview_card)
        preview_layout.setContentsMargins(16, 14, 16, 14)
        right_title = QLabel("Review the clip")
        right_title.setObjectName("sectionTitle")
        preview_layout.addWidget(right_title)
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumHeight(220)
        preview_layout.addWidget(self.video_widget, 1)
        self.caption_preview = QLabel("English subtitles appear here during playback.")
        self.caption_preview.setTextFormat(Qt.TextFormat.PlainText)
        self.caption_preview.setObjectName("previewText")
        self.caption_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.caption_preview.setWordWrap(True)
        self.caption_preview.setMinimumHeight(58)
        preview_layout.addWidget(self.caption_preview)
        playback = QHBoxLayout()
        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.toggle_play)
        playback.addWidget(self.play_button)
        self.seek = QSlider(Qt.Orientation.Horizontal)
        self.seek.sliderReleased.connect(self._seek_released)
        playback.addWidget(self.seek, 1)
        self.clock = QLabel("00:00 / 00:00")
        self.clock.setObjectName("muted")
        playback.addWidget(self.clock)
        preview_layout.addLayout(playback)
        note = QLabel(
            "Preview shows the original video; the English line is shown below it. Export burns subtitles into the MP4."
        )
        note.setObjectName("muted")
        note.setWordWrap(True)
        preview_layout.addWidget(note)
        self.external_button = QPushButton("Open original in video player")
        self.external_button.clicked.connect(self.open_original)
        preview_layout.addWidget(self.external_button)
        splitter.addWidget(preview_card)
        splitter.setSizes([685, 450])
        outer.addWidget(splitter, 1)

        footer = QHBoxLayout()
        self.open_project_button = QPushButton("Open draft")
        self.open_project_button.clicked.connect(self.open_draft)
        footer.addWidget(self.open_project_button)
        self.save_project_button = QPushButton("Save draft")
        self.save_project_button.clicked.connect(self.save_draft)
        footer.addWidget(self.save_project_button)
        footer.addStretch(1)
        self.srt_button = QPushButton("Save .srt")
        self.srt_button.clicked.connect(self.export_srt)
        footer.addWidget(self.srt_button)
        self.mp4_button = QPushButton("Export subtitled MP4")
        self.mp4_button.setObjectName("primary")
        self.mp4_button.clicked.connect(self.export_mp4)
        footer.addWidget(self.mp4_button)
        outer.addLayout(footer)

        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.audio_output.setVolume(0.7)
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.video_widget)
        self.player.positionChanged.connect(self._position_changed)
        self.player.durationChanged.connect(self._duration_changed)
        self.player.playbackStateChanged.connect(self._play_state_changed)
        self.player.errorOccurred.connect(self._media_error)

        self.setStyleSheet("""
            QWidget { background: #0b1422; color: #e7eff7; font-size: 13px; }
            QLabel, QCheckBox, QSlider { background: transparent; }
            QFrame#header { background: #15263a; border: 1px solid #29455d; border-radius: 14px; }
            QFrame#card { background: #111f30; border: 1px solid #263c52; border-radius: 12px; }
            QLabel#eyebrow { color: #69dac1; font-size: 11px; font-weight: bold; letter-spacing: 1px; }
            QLabel#title { font-size: 24px; font-weight: bold; }
            QLabel#sectionTitle { font-size: 17px; font-weight: bold; }
            QLabel#muted { color: #9eb1c2; }
            QLabel#badge { color: #8ef1d4; background: #173e41; padding: 9px 13px; border-radius: 11px; font-weight: bold; }
            QLabel#file { color: #d8e8f3; }
            QLabel#previewText { background: #172d3c; border-radius: 8px; color: white; padding: 8px; font-weight: bold; }
            QPushButton { background: #1c354b; border: 1px solid #33546a; border-radius: 7px; padding: 8px 13px; }
            QPushButton:hover { background: #284e66; }
            QPushButton#primary { background: #3cc9aa; border-color: #3cc9aa; color: #09202a; font-weight: bold; }
            QPushButton#primary:hover { background: #6be1c5; }
            QPushButton:disabled { color: #8192a0; background: #1b2b3a; border-color: #304151; }
            QLineEdit, QPlainTextEdit, QComboBox, QTableWidget {
                background: #0d1a2a; border: 1px solid #345066; border-radius: 6px; padding: 5px;
                selection-background-color: #256c74;
            }
            QTableWidget { gridline-color: #263b4f; alternate-background-color: #122336; }
            QHeaderView::section { background: #20354a; color: #c3d6e3; border: 0; padding: 8px; }
            QProgressBar { border: 0; background: #264053; border-radius: 3px; }
            QProgressBar::chunk { background: #42cfaf; border-radius: 3px; }
        """)

    def _refresh_buttons(self, *_args: object) -> None:
        ready = self.video is not None and self.rights.isChecked() and not self.busy
        has_lines = self.table.rowCount() > 0
        self.choose_button.setEnabled(not self.busy)
        self.model_select.setEnabled(not self.busy)
        self.french_check.setEnabled(not self.busy)
        self.cancel_button.setVisible(self.busy)
        self.rights.setEnabled(not self.busy)
        self.generate_button.setEnabled(ready)
        self.table.setEnabled(not self.busy)
        self.english_edit.setEnabled(ready and has_lines)
        self.start_edit.setEnabled(ready and has_lines)
        self.end_edit.setEnabled(ready and has_lines)
        self.add_button.setEnabled(ready)
        self.split_button.setEnabled(ready and self.table.currentRow() >= 0)
        self.merge_button.setEnabled(
            ready and 0 <= self.table.currentRow() < self.table.rowCount() - 1
        )
        self.delete_button.setEnabled(ready and self.table.currentRow() >= 0)
        self.open_project_button.setEnabled(not self.busy)
        self.save_project_button.setEnabled(ready and has_lines)
        self.srt_button.setEnabled(ready and has_lines)
        self.mp4_button.setEnabled(ready and has_lines)
        self.play_button.setEnabled(self.video is not None)
        self.external_button.setEnabled(self.video is not None)
        self.seek.setEnabled(self.video is not None)
        self.caption_count.setText(f"{self.table.rowCount()} lines")

    def _error(self, message: str) -> None:
        QMessageBox.warning(self, "ClipTranslate", message)

    def _confirm_overwrite(self, *paths: Path) -> bool:
        existing = [str(path) for path in paths if path.exists()]
        if not existing:
            return True
        answer = QMessageBox.question(
            self,
            "Replace existing file?",
            "This will replace:\n" + "\n".join(existing),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return answer == QMessageBox.StandardButton.Yes

    def choose_video(self) -> None:
        if (
            self.table.rowCount()
            and QMessageBox.question(
                self,
                "Change video?",
                "Changing videos discards the current subtitles. Save a draft first if needed.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            != QMessageBox.StandardButton.Yes
        ):
            return
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Choose a short French-language video",
            "",
            "Videos (*.mp4 *.mov *.mkv)",
        )
        if not filename:
            return
        try:
            video = probe_video(Path(filename))
        except ClipError as exc:
            self._error(str(exc))
            return
        self.video = video
        self.project_path = None
        self.processing_seconds = 0.0
        self.player.stop()
        self.player.setSource(QUrl.fromLocalFile(str(video.path)))
        self.file_label.setText(
            f"{video.path.name}  ·  {timecode(video.duration)[:-4]}  ·  {video.size / 1048576:.1f} MiB"
        )
        self.progress_label.setText("Ready. Confirm you have permission, then generate subtitles.")
        self.progress.setValue(0)
        self.rights.setChecked(False)
        self._set_captions([])
        self.dirty = False
        self._refresh_buttons()

    def _set_captions(self, captions: list[Caption]) -> None:
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        for caption in captions:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self._populate_row(row, caption)
        self.table.blockSignals(False)
        self.active_row = -1
        if captions:
            self._select_row(0)
        else:
            self._load_editor(-1)
            self.caption_preview.setText("English subtitles appear here during playback.")
        self._refresh_buttons()

    def _select_row(self, row: int) -> None:
        self.table.setCurrentCell(row, 3)
        # Qt may retain the same current cell when rows are merged/deleted. In that
        # case currentCellChanged is not emitted, so refresh the editor explicitly.
        if self.active_row != row:
            self._row_changed(row, 3, -1, -1)
        else:
            self._load_editor(row)

    def _populate_row(self, row: int, caption: Caption) -> None:
        for column, text in enumerate(
            [
                str(row + 1),
                timecode(caption.start),
                timecode(caption.end),
                caption.english,
            ]
        ):
            item = QTableWidgetItem(text)
            if column == 0:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item.setData(FRENCH_ROLE, caption.french)
            self.table.setItem(row, column, item)
        self.table.setRowHeight(row, 46)
        self._style_caption(row)

    def _style_caption(self, row: int) -> None:
        if not (0 <= row < self.table.rowCount()):
            return
        item = self.table.item(row, 3)
        if item is None:
            return
        try:
            start = parse_timecode(self.table.item(row, 1).text())
            end = parse_timecode(self.table.item(row, 2).text())
            seconds = max(end - start, 0.25)
        except ClipError:
            seconds = 0.25
        count = len(item.text().replace("\n", " ").strip())
        hard_to_read = count > 84 or count / seconds > 22
        previous = self._syncing
        self._syncing = True
        try:
            item.setForeground(QColor("#efbb72" if hard_to_read else "#e7eff7"))
            item.setToolTip(
                "Long or fast subtitle: review for readability." if hard_to_read else ""
            )
        finally:
            self._syncing = previous

    def _row_changed(self, row: int, _column: int, _old_row: int, _old_column: int) -> None:
        if row == self.active_row:
            return
        self.active_row = row
        self._load_editor(row)
        self._refresh_buttons()
        if row >= 0 and self.video is not None:
            try:
                start = parse_timecode(self.table.item(row, 1).text())
                self.player.pause()
                self.player.setPosition(round(start * 1000))
            except ClipError:
                pass

    def _load_editor(self, row: int) -> None:
        self._syncing = True
        try:
            self.english_edit.setPlainText(self.table.item(row, 3).text() if row >= 0 else "")
            self.start_edit.setText(self.table.item(row, 1).text() if row >= 0 else "")
            self.end_edit.setText(self.table.item(row, 2).text() if row >= 0 else "")
            french = self._french_at(row) if row >= 0 else ""
            self.french_label.setText(f"French heard: {french}" if french else "")
        finally:
            self._syncing = False

    def load_demo(self) -> None:
        """Open a synthetic clip with invented captions (no model needed) to try the editor."""
        self._demo_dir = tempfile.TemporaryDirectory(prefix="cliptranslate-demo-")
        video = create_demo_clip(Path(self._demo_dir.name))
        self.video = video
        self.project_path = None
        self.processing_seconds = 0.0
        self.player.setSource(QUrl.fromLocalFile(str(video.path)))
        self.setWindowTitle("ClipTranslate  •  DEMO MODE (invented sample captions)")
        self.file_label.setText(
            "DEMO: synthetic test clip with invented captions. This is not a real translation."
        )
        self.rights.setChecked(True)
        self._set_captions(demo_captions())
        self.dirty = False
        self.progress_label.setText(
            "Demo mode. Try editing, splitting, merging, saving a draft and exporting. "
            "Choose your own video for a real translation."
        )
        self._refresh_buttons()

    def _french_at(self, row: int) -> str:
        item = self.table.item(row, 0)
        return str(item.data(FRENCH_ROLE) or "") if item is not None else ""

    def _editor_changed(self, *_args: object) -> None:
        if self._syncing or self.active_row < 0 or self.active_row >= self.table.rowCount():
            return
        self._syncing = True
        try:
            for col, value in (
                (1, self.start_edit.text()),
                (2, self.end_edit.text()),
                (3, self.english_edit.toPlainText()),
            ):
                item = self.table.item(self.active_row, col)
                if item.text() != value:
                    item.setText(value)
                    self.dirty = True
        finally:
            self._syncing = False
        self._style_caption(self.active_row)
        self._position_changed(self.player.position())

    def _item_changed(self, item: QTableWidgetItem) -> None:
        if self._syncing:
            return
        self.dirty = True
        self._style_caption(item.row())
        if item.row() == self.active_row and item.column() in (1, 2, 3):
            self._load_editor(item.row())
        self._position_changed(self.player.position())

    def _captions_from_table(self) -> list[Caption]:
        if self.video is None:
            raise ClipError("Choose a video first.")
        captions = []
        for row in range(self.table.rowCount()):
            try:
                captions.append(
                    Caption(
                        start=parse_timecode(self.table.item(row, 1).text()),
                        end=parse_timecode(self.table.item(row, 2).text()),
                        english=self.table.item(row, 3).text(),
                        french=self._french_at(row),
                    )
                )
            except ClipError as exc:
                raise ClipError(f"Subtitle {row + 1}: {exc}") from exc
        validate_captions(captions, self.video.duration)
        return captions

    def add_line(self) -> None:
        """Let an editor restore dialogue that automatic recognition missed."""
        if self.video is None:
            return
        self.player.pause()
        start = 0.0
        end = min(self.video.duration, 2.0)
        row = self.table.currentRow()
        if row >= 0:
            try:
                start = parse_timecode(self.table.item(row, 2).text())
                end = min(self.video.duration, start + 2.0)
                if row + 1 < self.table.rowCount():
                    end = min(end, parse_timecode(self.table.item(row + 1, 1).text()))
                if end - start < 0.25:
                    start, end = 0.0, min(self.video.duration, 2.0)
            except ClipError:
                start, end = 0.0, min(self.video.duration, 2.0)
        dialog = QDialog(self)
        dialog.setWindowTitle("Add missing English subtitle")
        dialog.setMinimumWidth(460)
        form = QFormLayout(dialog)
        start_input = QLineEdit(timecode(start))
        end_input = QLineEdit(timecode(end))
        text_input = QPlainTextEdit()
        text_input.setPlaceholderText("English text for the missing dialogue…")
        text_input.setFixedHeight(80)
        form.addRow("Start (HH:MM:SS.mmm)", start_input)
        form.addRow("End (HH:MM:SS.mmm)", end_input)
        form.addRow("English subtitle", text_input)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)

        def insert() -> None:
            try:
                existing = self._captions_from_table() if self.table.rowCount() else []
                added = Caption(
                    parse_timecode(start_input.text()),
                    parse_timecode(end_input.text()),
                    text_input.toPlainText(),
                )
                combined = sorted([*existing, added], key=lambda item: item.start)
                validate_captions(combined, self.video.duration)
            except ClipError as exc:
                QMessageBox.warning(dialog, "Check the subtitle", str(exc))
                return
            self._set_captions(combined)
            self.dirty = True
            self._select_row(combined.index(added))
            dialog.accept()

        buttons.accepted.connect(insert)
        dialog.exec()

    def split_line(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            return
        try:
            caption = self._caption_at(row)
        except ClipError as exc:
            self._error(str(exc))
            return
        words = caption.english.split()
        if len(words) < 2 or caption.end - caption.start < 0.4:
            self._error(
                "Splitting needs at least two words and a subtitle at least 0.4 seconds long."
            )
            return
        middle = round((caption.start + caption.end) / 2, 3)
        self.table.blockSignals(True)
        self.table.item(row, 2).setText(timecode(middle))
        self.table.item(row, 3).setText(" ".join(words[: len(words) // 2]))
        self.table.insertRow(row + 1)
        self._populate_row(
            row + 1, Caption(middle, caption.end, " ".join(words[len(words) // 2 :]))
        )
        self._renumber()
        self.table.blockSignals(False)
        self.dirty = True
        self._style_caption(row)
        self._select_row(row + 1)
        self._refresh_buttons()

    def _caption_at(self, row: int) -> Caption:
        try:
            return Caption(
                parse_timecode(self.table.item(row, 1).text()),
                parse_timecode(self.table.item(row, 2).text()),
                self.table.item(row, 3).text(),
                self._french_at(row),
            )
        except ClipError as exc:
            raise ClipError(f"Subtitle {row + 1}: {exc}") from exc

    def merge_next(self) -> None:
        row = self.table.currentRow()
        if not 0 <= row < self.table.rowCount() - 1:
            return
        try:
            first = self._caption_at(row)
            second = self._caption_at(row + 1)
            if second.end <= first.start:
                raise ClipError("The second subtitle must end after the first starts.")
        except ClipError as exc:
            self._error(str(exc))
            return
        self.table.blockSignals(True)
        self.table.item(row, 2).setText(timecode(second.end))
        self.table.item(row, 3).setText(first.english.strip() + " " + second.english.strip())
        merged_french = " ".join(part for part in (first.french, second.french) if part)
        self.table.item(row, 0).setData(FRENCH_ROLE, merged_french)
        self.table.removeRow(row + 1)
        self._renumber()
        self.dirty = True
        self.table.blockSignals(False)
        self._style_caption(row)
        self.active_row = -1
        self._select_row(row)
        self._refresh_buttons()

    def delete_line(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            return
        if (
            QMessageBox.question(
                self,
                "Delete subtitle?",
                f"Delete subtitle {row + 1}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            != QMessageBox.StandardButton.Yes
        ):
            return
        self.table.blockSignals(True)
        self.table.removeRow(row)
        self._renumber()
        self.dirty = True
        self.table.blockSignals(False)
        self.active_row = -1
        if self.table.rowCount():
            self._select_row(min(row, self.table.rowCount() - 1))
        else:
            self._load_editor(-1)
        self._refresh_buttons()

    def _renumber(self) -> None:
        for row in range(self.table.rowCount()):
            self.table.item(row, 0).setText(str(row + 1))

    def generate_subtitles(self) -> None:
        if self.video is None or not self.rights.isChecked() or self.busy:
            return
        if (
            self.table.rowCount()
            and QMessageBox.question(
                self,
                "Replace subtitles?",
                "Generating again replaces your current edits. Save a draft first if needed.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            != QMessageBox.StandardButton.Yes
        ):
            return
        if not self._notice_shown:
            if (
                QMessageBox.question(
                    self,
                    "First-run model download",
                    "The speech model may download several hundred MB the first time you run it. "
                    "Subsequent runs use your local copy. Video and audio stay on your computer. Continue?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes,
                )
                != QMessageBox.StandardButton.Yes
            ):
                return
            self._notice_shown = True
        self.busy = True
        self._refresh_buttons()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        worker = TranslateWorker(
            self.video,
            self.model_select.currentData(),
            self.french_check.isChecked(),
            self,
        )
        self.worker = worker
        worker.updated.connect(self._progress_changed)
        worker.succeeded.connect(self._translation_done)
        worker.failed.connect(self._task_failed)
        worker.cancelled.connect(self._task_cancelled)
        worker.finished.connect(self._task_finished)
        worker.start()

    def _progress_changed(self, percent: int, message: str) -> None:
        if percent < 0:  # Work that cannot be measured, such as the first model download.
            self.progress.setRange(0, 0)
        else:
            self.progress.setRange(0, 100)
            self.progress.setValue(percent)
        self.progress_label.setText(message)

    def cancel_job(self) -> None:
        if self.worker is not None and self.worker.isRunning():
            self.worker.request_cancel()
            self.cancel_button.setEnabled(False)
            self.progress_label.setText("Cancelling… your existing subtitles are unchanged.")

    def _task_cancelled(self) -> None:
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress_label.setText("Cancelled. Your existing subtitles and files are unchanged.")

    def open_logs(self) -> None:
        folder = log_dir()
        folder.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

    def _translation_done(self, result: ProcessingResult) -> None:
        self._set_captions(result.captions)
        self.dirty = True  # New subtitles exist nowhere else until the editor saves them.
        self.processing_seconds = result.elapsed_seconds
        self.project_path = None
        self.progress_label.setText(
            f"{len(result.captions)} English subtitles in {result.elapsed_seconds:.0f}s. "
            "Review the text and timing before exporting."
        )
        self.progress.setValue(100)

    def _task_failed(self, message: str) -> None:
        self.progress_label.setText(
            "Could not finish. Your earlier edits and exports were not changed."
        )
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self._error(message)

    def _task_finished(self) -> None:
        self.busy = False
        self.worker = None
        self.cancel_button.setEnabled(True)
        self.progress.setRange(0, 100)
        self._refresh_buttons()

    def _recommended_name(self, extension: str) -> str:
        assert self.video is not None
        return str(self.video.path.with_name(self.video.path.stem + "_en" + extension))

    def export_srt(self) -> None:
        try:
            captions = self._captions_from_table()
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Save English subtitle file",
                self._recommended_name(".srt"),
                "SRT subtitles (*.srt)",
            )
            if not filename:
                return
            path = Path(filename)
            if not path.suffix:
                path = path.with_suffix(".srt")
            if not self._confirm_overwrite(path):
                return
            saved = save_srt(captions, self.video.duration, path)
            self.dirty = False
            self.progress_label.setText(
                f"Saved {saved.name}. English captions are ready to review in a video player."
            )
            QMessageBox.information(
                self, "Subtitles saved", f"English subtitles saved to:\n{saved}"
            )
        except ClipError as exc:
            self._error(str(exc))

    def export_mp4(self) -> None:
        try:
            captions = self._captions_from_table()
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Export MP4 with English subtitles",
                self._recommended_name(".mp4"),
                "MP4 video (*.mp4)",
            )
            if not filename:
                return
            path = Path(filename)
            if not path.suffix:
                path = path.with_suffix(".mp4")
            if not self._confirm_overwrite(path, path.with_suffix(".srt")):
                return
        except ClipError as exc:
            self._error(str(exc))
            return
        self.busy = True
        self._refresh_buttons()
        self.progress.setRange(0, 0)
        self.progress_label.setText(
            "Rendering MP4 with English subtitles… This may take a few minutes."
        )
        worker = ExportWorker(self.video, captions, path, self)
        self.worker = worker
        worker.succeeded.connect(self._export_done)
        worker.failed.connect(self._task_failed)
        worker.cancelled.connect(self._task_cancelled)
        worker.finished.connect(self._task_finished)
        worker.start()

    def _export_done(self, files: tuple[Path, Path]) -> None:
        mp4, srt = files
        self.dirty = False
        self.progress_label.setText(
            f"Exported {mp4.name} and {srt.name}. Ready to share after review."
        )
        QMessageBox.information(
            self,
            "Export complete",
            f"Subtitled video:\n{mp4}\n\nEditable subtitle file:\n{srt}",
        )

    def save_draft(self) -> bool:
        try:
            captions = self._captions_from_table()
            suggested = str(
                self.project_path or Path(self._recommended_name(".cliptranslate.json"))
            )
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Save editable draft",
                suggested,
                "ClipTranslate project (*.cliptranslate.json)",
            )
            if not filename:
                return False
            path = Path(filename)
            if not path.name.endswith(".cliptranslate.json") and not path.suffix:
                path = path.with_name(path.name + ".cliptranslate.json")
            if not self._confirm_overwrite(path):
                return False
            self.project_path = save_project(
                path,
                self.video,
                captions,
                self.model_select.currentData(),
                self.processing_seconds,
            )
            self.dirty = False
            self.progress_label.setText(f"Draft saved to {self.project_path.name}.")
            return True
        except ClipError as exc:
            self._error(str(exc))
            return False

    def open_draft(self) -> None:
        if (
            self.table.rowCount()
            and QMessageBox.question(
                self,
                "Open draft?",
                "Opening a draft replaces unsaved subtitle edits. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            != QMessageBox.StandardButton.Yes
        ):
            return
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Open editable draft",
            "",
            "ClipTranslate project (*.cliptranslate.json)",
        )
        if not filename:
            return
        try:
            project = load_project(Path(filename))
            video_path = project.video_path
            if not video_path.is_file():
                located, _ = QFileDialog.getOpenFileName(
                    self,
                    f"Find the original video ({video_path.name})",
                    str(video_path.parent if video_path.parent.is_dir() else ""),
                    "Videos (*.mp4 *.mov *.mkv)",
                )
                if not located:
                    return
                video_path = Path(located)
            video = probe_video(video_path)
            same_video = (
                video_fingerprint(video.path) == project.video_fingerprint
                if project.video_fingerprint
                else video.size == project.video_size
            )
            if not same_video or abs(video.duration - project.video_duration) > 0.1:
                raise ClipError(
                    "This is not the same video the draft was made from. Choose the original file."
                )
        except (ClipError, OSError) as exc:
            self._error(str(exc))
            return
        self.video = video
        self.project_path = Path(filename)
        self.processing_seconds = project.processing_seconds
        self.player.stop()
        self.player.setSource(QUrl.fromLocalFile(str(video.path)))
        self.file_label.setText(
            f"{video.path.name}  ·  {timecode(video.duration)[:-4]}  ·  {video.size / 1048576:.1f} MiB"
        )
        self.model_select.setCurrentIndex(max(0, self.model_select.findData(project.model_size)))
        self.rights.setChecked(False)
        self._set_captions(project.captions)
        self.dirty = False
        self.progress_label.setText("Draft opened. Confirm your rights again before exporting.")
        self.progress.setValue(0)
        self._refresh_buttons()

    def toggle_play(self) -> None:
        if self.video is None:
            return
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def _play_state_changed(self, state: QMediaPlayer.PlaybackState) -> None:
        self.play_button.setText(
            "Pause" if state == QMediaPlayer.PlaybackState.PlayingState else "Play"
        )

    def _duration_changed(self, milliseconds: int) -> None:
        self.seek.setMaximum(max(0, milliseconds))
        self._position_changed(self.player.position())

    def _position_changed(self, milliseconds: int) -> None:
        if not self.seek.isSliderDown():
            self.seek.setValue(max(0, milliseconds))
        length = self.player.duration()
        self.clock.setText(
            f"{timecode(max(0, milliseconds) / 1000)[:-4]} / {timecode(max(0, length) / 1000)[:-4]}"
        )
        current_text = "No English subtitle at this moment."
        for row in range(self.table.rowCount()):
            try:
                start = parse_timecode(self.table.item(row, 1).text())
                end = parse_timecode(self.table.item(row, 2).text())
            except ClipError:
                continue
            if start <= milliseconds / 1000 < end:
                current_text = self.table.item(row, 3).text() or "(empty subtitle)"
                break
        self.caption_preview.setText(current_text)

    def _seek_released(self) -> None:
        self.player.setPosition(self.seek.value())

    def _media_error(self, _error: QMediaPlayer.Error, _description: str) -> None:
        self.caption_preview.setText(
            "Video preview unavailable on this system. Export and SRT saving still work."
        )

    def open_original(self) -> None:
        if self.video is not None:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.video.path)))

    def closeEvent(self, event) -> None:
        if self.worker is not None and self.worker.isRunning():
            answer = QMessageBox.question(
                self,
                "A job is running",
                "Stop the running job and close? Nothing partial is saved.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            self.worker.request_cancel()
            self.worker.wait(15000)
        if self.dirty and self.table.rowCount():
            box = QMessageBox(self)
            box.setIcon(QMessageBox.Icon.Warning)
            box.setWindowTitle("Unsaved subtitles")
            box.setText("Your subtitle edits have not been saved.")
            save = box.addButton("Save draft", QMessageBox.ButtonRole.AcceptRole)
            box.addButton("Discard", QMessageBox.ButtonRole.DestructiveRole)
            cancel = box.addButton("Keep editing", QMessageBox.ButtonRole.RejectRole)
            box.setDefaultButton(save)
            box.exec()
            clicked = box.clickedButton()
            if clicked is cancel or (clicked is save and not self.save_draft()):
                event.ignore()
                return
        self.player.stop()
        super().closeEvent(event)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="cliptranslate", description="French to English subtitles for short videos."
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="open a synthetic sample clip with invented captions (no model download)",
    )
    options, qt_args = parser.parse_known_args(sys.argv[1:] if argv is None else argv)
    setup_logging()
    log.info("ClipTranslate started (demo=%s)", options.demo)
    app = QApplication([sys.argv[0], *qt_args])
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    if options.demo:
        window.load_demo()
    sys.exit(app.exec())
