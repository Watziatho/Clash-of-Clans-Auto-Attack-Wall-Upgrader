import sys
import subprocess
from pathlib import Path

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
            p = subprocess.Popen(
                cmd,
                creationflags=subprocess.CREATE_NEW_CONSOLE
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

def launch():
    import utils
    args = utils.parse_args()
    if args.gui: gui_launch(args)
    else: cmd_launch(args)
