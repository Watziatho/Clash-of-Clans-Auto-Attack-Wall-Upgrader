@echo off
title CoC Bot - Home Attack
cd /d E:\Projects\CoC_Bot
python src/main.py --instance-id main --gui
if %errorlevel% neq 0 (
    echo.
    echo Bot exited with an error.
    pause
)
