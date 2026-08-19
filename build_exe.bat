@echo off
title Build CoC Bot Executable
cd /d %~dp0
echo Building CoC_Bot.exe with PyInstaller...
pyinstaller --noconfirm --onedir --windowed --name "CoC_Bot" --add-data "assets;assets" --add-data "src/gui_server;gui_server" --paths "src" "src/main.py"
if %errorlevel% neq 0 (
    echo.
    echo Build failed!
    pause
    exit /b %errorlevel%
)
echo.
echo ========================================================
echo Build Succeeded! Executable is at: dist\CoC_Bot\CoC_Bot.exe
echo ========================================================
pause
