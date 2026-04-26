@echo off
setlocal enabledelayedexpansion

REM Go to project root (two levels up from build\windows\)
cd /d "%~dp0..\.."

echo ============================================================
echo   SRT-SUMMARIZER v2.0 - PyInstaller Build Script
echo ============================================================
echo.

set "APP_NAME=srt-summarizer-v2.0"
set "SPEC_FILE=srt_summarizer.spec"
set "DIST_DIR=dist"
set "BUILD_DIR=build"

REM ---- check Python --------------------------------------------------------
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found in PATH.
    pause
    exit /b 1
)
echo [INFO] Python found.

REM ---- install/upgrade build tools -----------------------------------------
echo.
echo [STEP 1] Installing PyInstaller...
python -m pip install --upgrade pyinstaller -q
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install PyInstaller.
    pause
    exit /b 1
)
echo [OK] PyInstaller installed.

REM ---- install runtime dependencies (web version) --------------------------
echo.
echo [STEP 2] Installing runtime dependencies...
python -m pip install -r requirements_web.txt -q
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)
echo [OK] Dependencies installed.

REM ---- verify bundled assets -----------------------------------------------
echo.
echo [STEP 3] Verifying bundled assets...

if not exist "HarmonyOS_Sans_SC_Medium.ttf" (
    echo [ERROR] Font file not found: HarmonyOS_Sans_SC_Medium.ttf
    pause
    exit /b 1
)
echo [OK] Font: HarmonyOS_Sans_SC_Medium.ttf

if not exist "vendor\ffmpeg\win64\ffmpeg.exe" (
    echo [ERROR] ffmpeg not found: vendor\ffmpeg\win64\ffmpeg.exe
    pause
    exit /b 1
)
echo [OK] ffmpeg: vendor\ffmpeg\win64\ffmpeg.exe

if not exist "templates\index.html" (
    echo [ERROR] Templates not found: templates\
    pause
    exit /b 1
)
echo [OK] Templates: templates\

if not exist "static\css\app.css" (
    echo [ERROR] Static assets not found: static\
    pause
    exit /b 1
)
echo [OK] Static assets: static\

if not exist "srt_summarizer\prompts\system.md" (
    echo [ERROR] System prompt not found: srt_summarizer\prompts\system.md
    pause
    exit /b 1
)
echo [OK] System prompt: srt_summarizer\prompts\system.md

REM ---- verify build metadata -----------------------------------------------
if not exist "%BUILD_DIR%\windows\version_info.txt" (
    echo [ERROR] version_info.txt not found.
    pause
    exit /b 1
)
echo [OK] Version info.

if not exist "%BUILD_DIR%\windows\file_version_info.txt" (
    echo [ERROR] file_version_info.txt not found.
    pause
    exit /b 1
)
echo [OK] File version info.

REM ---- clean previous build ------------------------------------------------
echo.
echo [STEP 4] Cleaning previous build...
if exist "%DIST_DIR%\%APP_NAME%.exe" del /q "%DIST_DIR%\%APP_NAME%.exe"
if exist "%BUILD_DIR%\%APP_NAME%" rmdir /s /q "%BUILD_DIR%\%APP_NAME%"
echo [OK] Cleaned.

REM ---- build ---------------------------------------------------------------
echo.
echo [STEP 5] Building single-file executable...
echo          This may take a few minutes...
echo.

python -m PyInstaller %SPEC_FILE% --noconfirm --clean --log-level=WARN
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] PyInstaller build failed!
    pause
    exit /b 1
)

REM ---- verify output -------------------------------------------------------
echo.
if exist "%DIST_DIR%\%APP_NAME%.exe" (
    for %%F in ("%DIST_DIR%\%APP_NAME%.exe") do (
        set "size_bytes=%%~zF"
        set /a "size_mb=!size_bytes! / 1048576"
    )
    echo ============================================================
    echo   BUILD SUCCESS
    echo ============================================================
    echo   Output : %DIST_DIR%\%APP_NAME%.exe
    echo   Size   : !size_mb! MB
    echo ============================================================
) else (
    echo [ERROR] Output not found: %DIST_DIR%\%APP_NAME%.exe
    pause
    exit /b 1
)

pause
endlocal
