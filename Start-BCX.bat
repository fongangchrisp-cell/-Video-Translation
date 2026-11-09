@echo off
rem ============================================================
rem  BCX ClipTranslate - Windows launcher. Double-click this file.
rem  First run: finds Python, builds a private environment, installs
rem  the app (needs internet, 5-15 min). Later runs: opens in seconds.
rem  Usage: Start-BCX.bat [demo | real | setup]
rem ============================================================
setlocal EnableExtensions
cd /d "%~dp0"
title BCX ClipTranslate
set "MODE=%~1"

echo.
echo  BCX (Black Cortex) - ClipTranslate
echo  ----------------------------------

rem ---- 1. Find a suitable Python (3.10, 3.11 or 3.12 only) ----
set "PY="
py -3.12 -c "import sys" >nul 2>&1 && set "PY=py -3.12"
if defined PY goto :havepython
py -3.11 -c "import sys" >nul 2>&1 && set "PY=py -3.11"
if defined PY goto :havepython
py -3.10 -c "import sys" >nul 2>&1 && set "PY=py -3.10"
if defined PY goto :havepython
python -c "import sys; sys.exit(0 if (3,10) <= sys.version_info[:2] <= (3,12) else 1)" >nul 2>&1 && set "PY=python"
if defined PY goto :havepython

echo.
echo  PROBLEM: Python 3.10, 3.11 or 3.12 was not found on this computer.
echo.
echo  What to do:
echo    1. Open https://www.python.org/downloads/ and download Python 3.12
echo       (NOT 3.13 or newer - the app does not support it yet).
echo    2. Run the installer. On the FIRST screen, tick "Add python.exe to PATH".
echo    3. Close this window and double-click Start-BCX.bat again.
echo.
pause
exit /b 1

:havepython
rem ---- 2. Create the private environment (.venv) if missing ----
if not exist ".venv\Scripts\python.exe" (
    echo  Creating a private environment in the .venv folder...
    %PY% -m venv .venv
    if errorlevel 1 goto :fail
)

rem ---- 3. Install the app if it is not installed (or the folder was moved) ----
".venv\Scripts\python.exe" -c "import PySide6, faster_whisper, imageio_ffmpeg, cliptranslate" >nul 2>&1
if errorlevel 1 (
    echo.
    echo  First-time setup: downloading and installing the app.
    echo  This needs internet and takes 5-15 minutes. Please wait and do not close this window.
    echo.
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    if errorlevel 1 goto :fail
    ".venv\Scripts\python.exe" -m pip install --prefer-binary -e .
    if errorlevel 1 goto :fail
    echo.
    echo  Setup finished.
)

if /i "%MODE%"=="setup" (
    echo  Setup is complete. Double-click Start-BCX.bat to open the app.
    exit /b 0
)

rem ---- 4. Choose what to open ----
if /i "%MODE%"=="demo" goto :rundemo
if /i "%MODE%"=="real" goto :runreal
echo.
echo   What do you want to open?
echo     1 = DEMO: try the editor with a sample clip (no download, invented captions)
echo     2 = REAL: translate my own French video (first time downloads the speech model)
echo.
choice /c 12 /n /m "  Type 1 or 2: "
if errorlevel 2 goto :runreal
goto :rundemo

:rundemo
echo  Opening the demo...
".venv\Scripts\python.exe" -m cliptranslate --demo
goto :done

:runreal
echo  Opening the app...
".venv\Scripts\python.exe" -m cliptranslate
goto :done

:done
if errorlevel 1 goto :fail
exit /b 0

:fail
echo.
echo  Something went wrong (see the messages above).
echo  Take a photo or screenshot of this window and send it to the BCX team.
echo.
pause
exit /b 1
