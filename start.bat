@echo off
cd /d "%~dp0"

python --version >nul 2>&1
if errorlevel 1 (
    echo Python not found!
    echo Please install Python 3 from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)

echo Python found.
echo.

echo Checking tkinter...
python -c "import tkinter" >nul 2>&1
if errorlevel 1 (
    echo ERROR: tkinter not found!
    echo Please reinstall Python and make sure to check "tcl/tk and IDLE" during install.
    pause
    exit /b 1
)
echo tkinter OK.

echo Installing dependencies...
pip install requests -q
if errorlevel 1 (
    echo ERROR: Failed to install requests. Check your internet connection.
    pause
    exit /b 1
)
echo requests OK.

echo.
echo Starting app...
python srt_summarizer.py

echo.
echo App closed. Press any key to exit.
pause
