@echo off
title [CoC Bot - base3]
cd /d E:\Projects\CoC_Bot
python -u src/main.py --instance-id base3 --no-gui
if %errorlevel% neq 0 (
    echo.
    echo Bot for base3 exited with an error.
    pause
)
