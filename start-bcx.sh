#!/usr/bin/env bash
# BCX ClipTranslate - macOS / Linux launcher.
# First run: finds Python, builds a private environment, installs the app
# (needs internet, 5-15 min). Later runs: opens in seconds.
# Usage: ./start-bcx.sh [demo | real | setup]
set -u
cd "$(dirname "$0")" || exit 1
MODE="${1:-}"

pause_and_exit() { echo; read -r -p "Press Enter to close this window..." _ || true; exit "${1:-1}"; }

echo
echo " BCX (Black Cortex) - ClipTranslate"
echo " ----------------------------------"

# 1. Find Python 3.10 / 3.11 / 3.12 only
PY=""
for candidate in python3.12 python3.11 python3.10 python3 python; do
    if command -v "$candidate" >/dev/null 2>&1 &&
        "$candidate" -c 'import sys; sys.exit(0 if (3,10) <= sys.version_info[:2] <= (3,12) else 1)' 2>/dev/null; then
        PY="$candidate"
        break
    fi
done
if [ -z "$PY" ]; then
    echo
    echo " PROBLEM: Python 3.10, 3.11 or 3.12 was not found."
    echo
    echo " What to do:"
    echo "   1. Open https://www.python.org/downloads/ and install Python 3.12"
    echo "      (NOT 3.13 or newer - the app does not support it yet)."
    echo "   2. Close this window and start this launcher again."
    pause_and_exit 1
fi

# 2. Private environment
if [ ! -x ".venv/bin/python" ]; then
    echo " Creating a private environment in the .venv folder..."
    "$PY" -m venv .venv || { echo " Could not create the environment."; pause_and_exit 1; }
fi
VPY=".venv/bin/python"

# 3. Install if needed (or if the folder was moved)
if ! "$VPY" -c "import PySide6, faster_whisper, imageio_ffmpeg, cliptranslate" >/dev/null 2>&1; then
    echo
    echo " First-time setup: downloading and installing the app."
    echo " This needs internet and takes 5-15 minutes. Please wait."
    echo
    "$VPY" -m pip install --upgrade pip &&
        "$VPY" -m pip install --prefer-binary -e . || {
        echo
        echo " Setup failed (see the messages above). Send a screenshot of this window to the BCX team."
        pause_and_exit 1
    }
    echo " Setup finished."
fi

if [ "$MODE" = "setup" ]; then
    echo " Setup is complete. Start this launcher again to open the app."
    exit 0
fi

# 4. Choose what to open
if [ -z "$MODE" ]; then
    echo
    echo "  What do you want to open?"
    echo "    1 = DEMO: try the editor with a sample clip (no download, invented captions)"
    echo "    2 = REAL: translate my own French video (first time downloads the speech model)"
    echo
    read -r -p "  Type 1 or 2, then Enter: " choice
    case "$choice" in 2) MODE=real ;; *) MODE=demo ;; esac
fi

if [ "$MODE" = "demo" ]; then
    echo " Opening the demo..."
    "$VPY" -m cliptranslate --demo
else
    echo " Opening the app..."
    "$VPY" -m cliptranslate
fi
status=$?
if [ "$status" -ne 0 ]; then
    echo
    echo " Something went wrong (see the messages above). Send a screenshot to the BCX team."
    pause_and_exit "$status"
fi
