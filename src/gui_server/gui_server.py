import sys
import json
from pathlib import Path

if hasattr(sys, "_MEIPASS"):
    path = Path(sys._MEIPASS) / "gui_server"
else:
    path = Path(__file__).parent.resolve()
    sys.path.append(str(path.parent))

sys.path.append(str(path))

import os
import time
import logging
from flask import Flask, render_template, jsonify, abort, request

# Silence Flask access log spam
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

try:
    from configs import *
except:
    from configs_build import *

app = Flask(__name__)
bot_pipe = None

def get_instance_port(inst_id):
    internal_name = "Pie64"
    mim_path = Path(r"C:\ProgramData\BlueStacks_nxt\Engine\UserData\MimMetaData.json")
    if mim_path.exists():
        try:
            mim_data = json.loads(mim_path.read_text())
            instances_map = {instance['Name']: instance["InstanceName"] for instance in mim_data.get("Organization", [])}
            internal_name = instances_map.get(inst_id, "Pie64")
        except:
            pass
    
    conf_path = Path(r"C:\ProgramData\BlueStacks_nxt\bluestacks.conf")
    if conf_path.exists():
        try:
            for l in conf_path.read_text().splitlines():
                if l.startswith(f"bst.instance.{internal_name}.adb_port"):
                    return l.split("=")[1].strip().replace('"', '')
        except:
            pass
    return "5555"

class Instance:
    def __init__(self, id=None):
        self.id = id if id is not None else ""
        self.run_status = "Running"
        self.end_time = 0
        self.is_paused = False
        task_settings = {
            "home_attacks": not ATTACK_HOME_BASE,
        }
        self.exclusions = set(k for k, v in task_settings.items() if v)

instances = {}

@app.route("/", methods=["GET"])
def home():
    instance_info = []
    for inst_id in INSTANCE_IDS:
        is_running = inst_id in instances
        is_paused = instances[inst_id].is_paused if is_running else False
        adb_p = get_instance_port(inst_id)
        
        if not is_running:
            display_status = "Idle"
        elif is_paused:
            display_status = "Paused"
        else:
            display_status = instances[inst_id].run_status if instances[inst_id].run_status else "Running"
            
        instance_info.append({
            "id": inst_id,
            "running": is_running,
            "paused": is_paused,
            "port": adb_p,
            "status": display_status
        })
    return render_template(
        "home.html",
        instances=instance_info,
        all_ids=INSTANCE_IDS,
        active_ids=list(instances.keys()),
        ids=sorted(list(instances.keys())),
    )

@app.route("/instances/<id>", methods=["GET"])
def handle_instance(id):
    instance = instances.get(id)
    if not instance:
        instance = Instance(id)
        instances[id] = instance
        if bot_pipe:
            bot_pipe.send({"action": "start", "id": id})
            
    return render_template(
        "instance.html",
        id=id,
        web_app_url=WEB_APP_URL,
        end_time=instance.end_time,
        current_time=time.time(),
        run_status=instance.run_status,
        exclusions=list(instance.exclusions),
    )

@app.route("/instance_action", methods=["POST"])
def handle_instance_start_stop():
    data = request.json
    action = data.get("action", "")
    id = data.get("id", "")
    
    if action == "start":
        if id not in INSTANCE_IDS:
            return jsonify(0)
        if id not in instances:
            instances[id] = Instance(id)
            if bot_pipe:
                bot_pipe.send({"action": "start", "id": id})
        else:
            instances[id].is_paused = False
            instances[id].run_status = "Running"
        return jsonify(1)
        
    elif action == "pause":
        if id in instances:
            instances[id].is_paused = True
            instances[id].run_status = "Paused"
            return jsonify(1)
        return jsonify(0)
        
    elif action == "resume":
        if id in instances:
            instances[id].is_paused = False
            instances[id].run_status = "Running"
            return jsonify(1)
        return jsonify(0)
        
    elif action == "stop":
        instance = instances.pop(id, None)
        if instance:
            if bot_pipe:
                bot_pipe.send({"action": "stop", "id": id})
        return jsonify(1)
        
    return jsonify(0)

@app.route("/current_time", methods=["GET"])
def handle_current_time():
    return {"current_time": time.time()}

@app.route("/instances/<id>/end_time", methods=["GET", "POST"])
def handle_end_time(id):
    instance = instances.get(id)
    if not instance: abort(404)
    if request.method == "POST":
        data = request.json.get("time", 0)
        instance.end_time = int(data) * 60 + time.time()
    return {"end_time": instance.end_time}

@app.route("/instances/<id>/running", methods=["GET"])
def handle_running(id):
    instance = instances.get(id)
    if not instance:
        return {"running": False, "paused": False}
    time_active = (instance.end_time == 0 or instance.end_time > time.time())
    is_running = time_active and not getattr(instance, "is_paused", False)
    return {"running": is_running, "paused": getattr(instance, "is_paused", False)}

@app.route("/instances/<id>/status", methods=["GET", "POST"])
def handle_status(id):
    instance = instances.get(id)
    if not instance: abort(404)
    if request.method == "POST":
        data = request.json
        instance.run_status = data.get("status", "")
    return {"status": instance.run_status, "paused": getattr(instance, "is_paused", False)}

@app.route("/instances/<id>/exclude", methods=["GET", "POST"])
def handle_exclude(id):
    instance = instances.get(id)
    if not instance: abort(404)
    if request.method == "POST":
        data = request.json
        exclude = data.get("exclude", None)
        task = data.get("task", None)
        if exclude is None: abort(400)
        if exclude:
            instance.exclusions.add(task)
        else:
            instance.exclusions.discard(task)
    return {"exclusions": list(instance.exclusions)}

@app.route("/instances/<id>/logs", methods=["GET"])
def handle_instance_logs(id):
    log_path = Path("debug") / f"{id}.log"
    if not log_path.exists():
        app_data_log = Path.home() / ".CoC_Bot" / "debug" / f"{id}.log"
        if app_data_log.exists():
            log_path = app_data_log

    if log_path.exists():
        try:
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
                return jsonify({"logs": lines[-300:], "count": len(lines)})
        except Exception as e:
            return jsonify({"logs": [f"Error reading log: {e}"], "count": 0})
    return jsonify({"logs": ["No logs recorded yet. Click START to begin."], "count": 0})

@app.route("/instances/<id>/logs/clear", methods=["POST"])
def handle_clear_logs(id):
    log_path = Path("debug") / f"{id}.log"
    if log_path.exists():
        try:
            with open(log_path, "w", encoding="utf-8") as f:
                f.write("")
        except:
            pass
    return jsonify(1)

def log_instance_message(inst_id, message):
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_msg = f"{timestamp} | INFO | {message}\n"
    
    for base_dir in [Path("debug"), Path.home() / ".CoC_Bot" / "debug"]:
        try:
            p = base_dir / f"{inst_id}.log"
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, "a", encoding="utf-8", errors="replace") as f:
                f.write(formatted_msg)
        except:
            pass

@app.route("/instances/<id>/wall_config", methods=["GET", "POST"])
def handle_wall_config(id):
    instance = instances.get(id)
    cfg_file = Path("debug") / f"{id}_wall_config.json"
    
    if request.method == "POST":
        data = request.json or {}
        if instance:
            if "auto_upgrade_walls" in data:
                instance.auto_upgrade_walls = bool(data["auto_upgrade_walls"])
            if "wall_resource_preference" in data:
                instance.wall_resource_preference = str(data["wall_resource_preference"])
            if "min_resource_reserve" in data:
                instance.min_resource_reserve = int(data["min_resource_reserve"])
            if "min_wall_trigger_loot" in data:
                instance.min_wall_trigger_loot = int(data["min_wall_trigger_loot"])
                
        auto_up = getattr(instance, "auto_upgrade_walls", True) if instance else bool(data.get("auto_upgrade_walls", True))
        pref = getattr(instance, "wall_resource_preference", "ANY") if instance else str(data.get("wall_resource_preference", "ANY"))
        res = getattr(instance, "min_resource_reserve", 500000) if instance else int(data.get("min_resource_reserve", 500000))
        trig = getattr(instance, "min_wall_trigger_loot", 6000000) if instance else int(data.get("min_wall_trigger_loot", 6000000))

        # Persist to disk
        try:
            cfg_file.parent.mkdir(parents=True, exist_ok=True)
            with open(cfg_file, "w", encoding="utf-8") as f:
                json.dump({
                    "auto_upgrade_walls": auto_up,
                    "wall_resource_preference": pref,
                    "min_resource_reserve": res,
                    "min_wall_trigger_loot": trig
                }, f, indent=2)
        except:
            pass
            
        # Log to live instance terminal
        status_str = "ENABLED" if auto_up else "DISABLED"
        log_instance_message(id, f"⚙️ Auto-Wall Config Saved: [{status_str}] Min Trigger = {trig:,} | Reserve = {res:,} | Pref = {pref}")
            
        return jsonify({"success": True})
        
    # GET request
    if cfg_file.exists():
        try:
            with open(cfg_file, "r", encoding="utf-8") as f:
                saved = json.load(f)
                if instance:
                    instance.auto_upgrade_walls = saved.get("auto_upgrade_walls", True)
                    instance.wall_resource_preference = saved.get("wall_resource_preference", "ANY")
                    instance.min_resource_reserve = saved.get("min_resource_reserve", 500000)
                    instance.min_wall_trigger_loot = saved.get("min_wall_trigger_loot", 6000000)
                return jsonify(saved)
        except:
            pass
            
    if not instance:
        return jsonify({
            "auto_upgrade_walls": True,
            "wall_resource_preference": "ANY",
            "min_resource_reserve": 500000,
            "min_wall_trigger_loot": 6000000
        })
    return jsonify({
        "auto_upgrade_walls": getattr(instance, "auto_upgrade_walls", True),
        "wall_resource_preference": getattr(instance, "wall_resource_preference", "ANY"),
        "min_resource_reserve": getattr(instance, "min_resource_reserve", 500000),
        "min_wall_trigger_loot": getattr(instance, "min_wall_trigger_loot", 6000000)
    })

def start_server(pipe, server_port=5000, id=None, debug=False):
    global bot_pipe
    bot_pipe = pipe
    if id: instances[id] = Instance(id)
    app.run(port=server_port, debug=debug)
