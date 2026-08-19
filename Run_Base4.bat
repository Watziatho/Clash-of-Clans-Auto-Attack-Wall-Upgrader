@echo off
title [CoC Bot - base4]
cd /d E:\Projects\CoC_Bot
python -u src/main.py --instance-id base4 --no-gui
if %errorlevel% neq 0 (
    echo.
    echo Bot for base4 exited with an error.
    pause
)
