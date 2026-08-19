@echo off
title [CoC Bot - main]
cd /d E:\Projects\CoC_Bot
python -u src/main.py --instance-id main --no-gui
if %errorlevel% neq 0 (
    echo.
    echo Bot for main exited with an error.
    pause
)
