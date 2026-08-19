@echo off
title CoC Bot - Multi Launcher
cd /d E:\Projects\CoC_Bot
echo Launching all 4 bases in separate console windows...
start "[CoC Bot - main]" cmd /k "cd /d E:\Projects\CoC_Bot && python -u src/main.py --instance-id main --no-gui"
start "[CoC Bot - base2]" cmd /k "cd /d E:\Projects\CoC_Bot && python -u src/main.py --instance-id base2 --no-gui"
start "[CoC Bot - base3]" cmd /k "cd /d E:\Projects\CoC_Bot && python -u src/main.py --instance-id base3 --no-gui"
start "[CoC Bot - base4]" cmd /k "cd /d E:\Projects\CoC_Bot && python -u src/main.py --instance-id base4 --no-gui"
echo All 4 bots launched!
