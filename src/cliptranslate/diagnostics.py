"""Local-only log file so a failed creator session can be diagnosed.

Nothing is uploaded. Logs hold timings, file names and error details, never subtitle text.
"""

from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOGGER_NAME = "cliptranslate"


def log_dir() -> Path:
    override = os.environ.get("CLIPTRANSLATE_LOG_DIR")
    if override:
        return Path(override).expanduser().resolve()
    if sys.platform == "win32":
        return Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "ClipTranslate" / "logs"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Logs" / "ClipTranslate"
    return Path.home() / ".local" / "state" / "cliptranslate" / "logs"


def setup_logging() -> Path | None:
    """Create the rotating log file; return its path, or None if it cannot be written."""
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    for handler in logger.handlers:
        if isinstance(handler, RotatingFileHandler):
            return Path(handler.baseFilename)
    try:
        folder = log_dir()
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / "cliptranslate.log"
        handler = RotatingFileHandler(path, maxBytes=512_000, backupCount=3, encoding="utf-8")
    except OSError:
        return None
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(message)s", "%Y-%m-%d %H:%M:%S")
    )
    logger.addHandler(handler)
    return path


def get_logger() -> logging.Logger:
    return logging.getLogger(LOGGER_NAME)
