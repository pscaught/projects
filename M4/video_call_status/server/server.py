#!/usr/bin/env python3

from flask import Flask, jsonify
import json
import threading
import subprocess
import time

debug = False

app = Flask(__name__)


@app.route("/")
def index():
    return app.send_static_file("index.html")


@app.route("/data.json")
def data():
    with open("data.json", "r") as f:
        data = json.load(f)
    return jsonify(data)


def write_file(_data):
    with open("data.json", "w") as f:
        f.write(json.dumps(_data))


def update_data():
    cmd = [
        "log",
        "stream",
        "--predicate",
        '(subsystem contains "com.apple.UVCExtension" and composedMessage contains "Post PowerLog") || eventMessage contains "Post event kCameraStream" || composedMessage contains "numRunningAudioEngines"',
    ]

    stream = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    global debug
    builtin_camera = False
    previous_microphone_state = ""
    previous_camera_state = ""
    usb_camera = False
    microphone = False

    data = {"camActive": False, "micActive": False}

    for l in stream.stdout:
        line = l.decode("utf-8").rstrip()

        # Microphone
        if "numRunningAudioEngines =" in line:
            try:
                if int(line[-1]) > 0:
                    microphone = True
                else:
                    microphone = False
            except ValueError:
                continue
            if microphone:
                microphone_state = "active"
                data["micActive"] = True
            else:
                microphone_state = "not active"
                data["micActive"] = False

            if microphone_state is not previous_microphone_state:
                if debug:
                    print(f"Microphone is {microphone_state}")
                write_file(data)
                previous_microphone_state = microphone_state

        # Camera
        if "kCameraStreamStart" in line:
            builtin_camera = True
        if '"VDCAssistant_Power_State" = On;' in line:
            usb_camera = True
        if "kCameraStreamStop" in line:
            builtin_camera = False
        if '"VDCAssistant_Power_State" = Off;' in line:
            usb_camera = False

        if usb_camera or builtin_camera:
            camera_state = "active"
            data["camActive"] = True
        else:
            camera_state = "not active"
            data["camActive"] = False
        if camera_state is not previous_camera_state:
            if debug:
                print(f"Camera is {camera_state}")
            write_file(data)
            previous_camera_state = camera_state


update_thread = threading.Thread(target=update_data)
update_thread.start()

if __name__ == "__main__":
    app.run(host="192.168.10.10", port=8000, debug=debug)
