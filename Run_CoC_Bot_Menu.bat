@echo off
title CoC Bot - Base Selector
cd /d E:\Projects\CoC_Bot
:menu
cls
echo ========================================================
echo             CLASH OF CLANS BOT - BASE SELECTOR
echo ========================================================
echo.
echo   [1] Run 'main' only        (Port 5555)
echo   [2] Run 'base2' only       (Port 5575)
echo   [3] Run 'base3' only       (Port 5585)
echo   [4] Run 'base4' only       (Port 5595)
echo   [5] Run ALL 4 bases simultaneously
echo   [6] Run 'base2' + 'base4' only
echo   [7] Run Desktop GUI (Manage all 4 in single window)
echo   [8] Exit
echo.
echo ========================================================
set /p choice="Select an option (1-8): "

if "%choice%"=="1" (
    start "[CoC Bot - main]" cmd /k "cd /d E:\Projects\CoC_Bot && python -u src/main.py --instance-id main --no-gui"
    goto menu
)
if "%choice%"=="2" (
    start "[CoC Bot - base2]" cmd /k "cd /d E:\Projects\CoC_Bot && python -u src/main.py --instance-id base2 --no-gui"
    goto menu
)
if "%choice%"=="3" (
    start "[CoC Bot - base3]" cmd /k "cd /d E:\Projects\CoC_Bot && python -u src/main.py --instance-id base3 --no-gui"
    goto menu
)
if "%choice%"=="4" (
    start "[CoC Bot - base4]" cmd /k "cd /d E:\Projects\CoC_Bot && python -u src/main.py --instance-id base4 --no-gui"
    goto menu
)
if "%choice%"=="5" (
    start "[CoC Bot - main]" cmd /k "cd /d E:\Projects\CoC_Bot && python -u src/main.py --instance-id main --no-gui"
    start "[CoC Bot - base2]" cmd /k "cd /d E:\Projects\CoC_Bot && python -u src/main.py --instance-id base2 --no-gui"
    start "[CoC Bot - base3]" cmd /k "cd /d E:\Projects\CoC_Bot && python -u src/main.py --instance-id base3 --no-gui"
    start "[CoC Bot - base4]" cmd /k "cd /d E:\Projects\CoC_Bot && python -u src/main.py --instance-id base4 --no-gui"
    goto menu
)
if "%choice%"=="6" (
    start "[CoC Bot - base2]" cmd /k "cd /d E:\Projects\CoC_Bot && python -u src/main.py --instance-id base2 --no-gui"
    start "[CoC Bot - base4]" cmd /k "cd /d E:\Projects\CoC_Bot && python -u src/main.py --instance-id base4 --no-gui"
    goto menu
)
if "%choice%"=="7" (
    python src/main.py --gui
    goto menu
)
if "%choice%"=="8" (
    exit
)
goto menu
