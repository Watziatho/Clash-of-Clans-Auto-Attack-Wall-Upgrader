@echo off
title [CoC Bot - base2]
cd /d E:\Projects\CoC_Bot
python -u src/main.py --instance-id base2 --no-gui
if %errorlevel% neq 0 (
    echo.
    echo Bot for base2 exited with an error.
    pause
)
