@echo off
title CoC Bot Manager
cd /d E:\Projects\CoC_Bot
python src/main.py --gui
if %errorlevel% neq 0 (
    echo.
    echo Bot exited with an error.
    pause
)
