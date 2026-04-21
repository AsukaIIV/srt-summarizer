@echo off
setlocal
cd /d "%~dp0\..\.."

set "FFMPEG_EXE=vendor\ffmpeg\win64\ffmpeg.exe"
if not exist "%FFMPEG_EXE%" (
    echo ERROR: Missing bundled ffmpeg at %FFMPEG_EXE%
    echo Please place ffmpeg.exe there before building.
    exit /b 1
)

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found.
    exit /b 1
)

python -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

python -m pip install pyinstaller
if errorlevel 1 exit /b 1

python -m PyInstaller --noconfirm --clean srt_summarizer.spec
if errorlevel 1 exit /b 1

echo.
echo Build completed: dist\SRT SUMMARIZER.exe
endlocal
