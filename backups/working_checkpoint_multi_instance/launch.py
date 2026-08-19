import sys
import os
import subprocess
from pathlib import Path
import psutil

def cleanup_orphan_bots():
    current_pid = os.getpid()
    for p in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if p.info['pid'] != current_pid and p.info['name'] in ['python.exe', 'python']:
                cmd = ' '.join(p.info['cmdline'] or [])
                if 'main.py' in cmd and ('--instance-id' in cmd or '--no-gui' in cmd):
                    p.kill()
        except:
            pass

def reset_log_files():
    debug_dir = Path("debug")
    if debug_dir.exists():
        for log_file in debug_dir.glob("*.log"):
            try:
                log_file.write_text("")
            except:
                pass
    app_data_debug = Path.home() / ".CoC_Bot" / "debug"
    if app_data_debug.exists():
        for log_file in app_data_debug.glob("*.log"):
            try:
                log_file.write_text("")
            except:
                pass

def launch_proc(args):
    from log import enable_logging
    from utils import parse_args, init_instance
    from coc_bot import CoC_Bot
    
    parse_args(args.debug, args.id, args.gui, args.gui_port)
    init_instance(args.id)
    enable_logging(args.id)
    bot = CoC_Bot()
    bot.run()

def cmd_launch(args):
    import utils
    if utils.DISABLE_DEVICE_SLEEP: utils.disable_sleep()
    launch_proc(args)

def gui_launch(args):
    from multiprocessing import Process
    import utils
    from gui import init_gui, get_gui
    
    cleanup_orphan_bots()
    reset_log_files()
    procs = {}
    pipe = init_gui(args.id)
    args.gui_port = get_gui().server_port
    
    if utils.DISABLE_DEVICE_SLEEP: Process(target=utils.disable_sleep).start()

    def start_instance_process(inst_id):
        main_script = Path(__file__).parent / "main.py"
        cmd = [
            sys.executable, "-u", str(main_script),
            "--instance-id", inst_id,
            "--no-gui",
            "--gui-port", str(args.gui_port)
        ]
        if sys.platform == "win32":
            CREATE_NO_WINDOW = 0x08000000
            p = subprocess.Popen(
                cmd,
                creationflags=CREATE_NO_WINDOW
            )
        else:
            p = subprocess.Popen(cmd)
        procs[inst_id] = p

    if args.id is not None:
        start_instance_process(args.id)

    try:
        while True:
            data = pipe.recv()
            if data == -1: raise SystemExit
            action, inst_id = data.get("action"), data.get("id")
            if action == "start" and inst_id:
                if inst_id not in procs or procs[inst_id].poll() is not None:
                    start_instance_process(inst_id)
            elif action == "stop" and inst_id:
                p = procs.pop(inst_id, None)
                if p and p.poll() is None:
                    p.terminate()
                    p.kill()
    except (EOFError, KeyboardInterrupt, SystemExit):
        get_gui().stop()
        pipe.close()
        for p in procs.values():
            if p and p.poll() is None:
                p.terminate()
                p.kill()
        cleanup_orphan_bots()

def launch():
    import utils
    args = utils.parse_args()
    if args.gui: gui_launch(args)
    else: cmd_launch(args)
