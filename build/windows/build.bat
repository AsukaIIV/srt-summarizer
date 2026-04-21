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

set "BUILT_EXE="
for %%F in (dist\SRT-SUMMARIZER-v*.exe) do set "BUILT_EXE=%%~nxF"
if not defined BUILT_EXE (
    echo ERROR: Built exe not found in dist
    exit /b 1
)

echo.
echo Build completed: dist\%BUILT_EXE%
endlocal
