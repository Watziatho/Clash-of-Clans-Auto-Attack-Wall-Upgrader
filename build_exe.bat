@echo off
title Build CoC Bot Executable v1.6.1
cd /d %~dp0
echo ========================================================
echo Building CoC_Bot_v1.6.1.exe with PyInstaller...
echo ========================================================

pyinstaller --noconfirm --onedir --windowed ^
    --icon "assets/icon.ico" ^
    --name "CoC_Bot_v1.6.1" ^
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
echo Build Succeeded! Executable is at: dist\CoC_Bot_v1.6.1\CoC_Bot_v1.6.1.exe
echo ========================================================
