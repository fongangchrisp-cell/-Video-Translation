"""Entry point for the packaged (PyInstaller) BCX ClipTranslate application.

Also supports ``--smoke-test``: a headless self-check used by the build pipeline to prove the
packaged app really contains Qt, the speech library and a working FFmpeg with subtitle support.
"""

from __future__ import annotations

import os
import sys

# A windowed app on Windows has no console: stdout/stderr are None, and libraries that print
# progress bars (model download) would crash. Give them somewhere harmless to write.
for _name in ("stdout", "stderr"):
    if getattr(sys, _name) is None:
        setattr(sys, _name, open(os.devnull, "w", encoding="utf-8"))  # noqa: SIM115


def smoke_test() -> int:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    import tempfile
    from pathlib import Path

    import ctranslate2  # noqa: F401
    import faster_whisper  # noqa: F401
    from PySide6.QtWidgets import QApplication

    from cliptranslate.demo import create_demo_clip, demo_captions
    from cliptranslate.gui import MainWindow
    from cliptranslate.media import export_video

    app = QApplication([sys.argv[0]])
    with tempfile.TemporaryDirectory() as folder:
        window = MainWindow()
        window.load_demo()
        app.processEvents()
        window.close()
        video = create_demo_clip(Path(folder))
        out = Path(folder) / "out.mp4"
        export_video(video, demo_captions(), out)
        assert out.is_file() and out.stat().st_size > 10_000, "export produced no video"
    print("SMOKE TEST OK")
    return 0


if __name__ == "__main__":
    if "--smoke-test" in sys.argv:
        sys.exit(smoke_test())
    from cliptranslate.gui import main

    main()
