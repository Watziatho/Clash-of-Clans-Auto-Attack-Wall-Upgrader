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
from flask import Flask, render_template, jsonify, abort, request
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
        adb_p = get_instance_port(inst_id)
        instance_info.append({
            "id": inst_id,
            "running": is_running,
            "port": adb_p,
            "status": instances[inst_id].run_status if is_running else "Stopped"
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
        return jsonify(1)
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
    if not instance: abort(404)
    return {"running": instance.end_time == 0 or instance.end_time < time.time()}

@app.route("/instances/<id>/status", methods=["GET", "POST"])
def handle_status(id):
    instance = instances.get(id)
    if not instance: abort(404)
    if request.method == "POST":
        data = request.json
        instance.run_status = data.get("status", "")
    return {"status": instance.run_status}

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

def start_server(pipe, server_port=5000, id=None, debug=False):
    global bot_pipe
    bot_pipe = pipe
    if id: instances[id] = Instance(id)
    app.run(port=server_port, debug=debug)
