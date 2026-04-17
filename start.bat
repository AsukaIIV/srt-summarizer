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
python -m pip install -r requirements.txt -q
if errorlevel 1 (
    echo ERROR: Failed to install dependencies. Check your internet connection.
    pause
    exit /b 1
)
echo dependencies OK.

echo.
echo Checking ffmpeg...
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo ffmpeg not found in current PATH. Refreshing PATH and checking again...
    set "PATH=%PATH%;%ProgramFiles%\ffmpeg\bin;%ProgramFiles(x86)%\ffmpeg\bin;%LOCALAPPDATA%\Microsoft\WinGet\Packages"
    ffmpeg -version >nul 2>&1
    if errorlevel 1 (
        echo ffmpeg still not found. Trying to install with winget...
        winget --version >nul 2>&1
        if errorlevel 1 (
            echo ERROR: winget not found, cannot auto-install ffmpeg.
            echo Please install ffmpeg manually, then run start.bat again.
            pause
            exit /b 1
        )

        winget install --id Gyan.FFmpeg --exact --accept-source-agreements --accept-package-agreements
        if errorlevel 1 (
            echo ERROR: Failed to auto-install ffmpeg with winget.
            echo Please install ffmpeg manually, then run start.bat again.
            pause
            exit /b 1
        )

        echo Refreshing PATH and re-checking ffmpeg...
        set "PATH=%PATH%;%ProgramFiles%\ffmpeg\bin;%ProgramFiles(x86)%\ffmpeg\bin;%LOCALAPPDATA%\Microsoft\WinGet\Packages"
        ffmpeg -version >nul 2>&1
        if errorlevel 1 (
            echo ERROR: ffmpeg was installed but is not available in current PATH yet.
            echo Please reopen this script after installation completes.
            pause
            exit /b 1
        )
    ) else (
        echo ffmpeg found after refreshing PATH.
    )
)
echo ffmpeg OK.


echo.
echo Starting app...
python app.py

echo.
echo App closed. Press any key to exit.
pause
