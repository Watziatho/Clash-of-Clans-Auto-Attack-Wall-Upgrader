@echo off
title Build CoC Bot Standalone Executable v1.6.3
cd /d %~dp0
echo ========================================================
echo Building Standalone (Single File) CoC_Bot_v1.6.3.exe...
echo ========================================================

pyinstaller --noconfirm --onefile --windowed ^
    --icon "assets/icon.ico" ^
    --name "CoC_Bot_v1.6.3" ^
    --add-data "assets;assets" ^
    --add-data "src/gui_server;gui_server" ^
    --collect-all "rapidocr_onnxruntime" ^
    --collect-all "webview" ^
    --paths "src" ^
    "src/main.py"

if %errorlevel% neq 0 (
    echo.
    echo Build failed!
    pause
    exit /b %errorlevel%
)

echo.
echo ========================================================
echo Build Succeeded! Standalone Executable is at: dist\CoC_Bot_v1.6.3.exe
echo ========================================================
