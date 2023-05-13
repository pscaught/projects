#!/usr/bin/env python3
"""Monitor whether a camera or microphone is active on macOS"""

import json
import threading
import subprocess
from flask import Flask, jsonify

DEBUG = False

app = Flask(__name__)


@app.route("/")
def index():
    """Placeholder index.html"""
    return app.send_static_file("index.html")


@app.route("/data.json")
def get_data():
    """Read from json file and serve the contents at /data.json"""
    with open("data.json", "r", encoding="utf-8") as _f:
        _data = json.load(_f)
    return jsonify(_data)


def write_file(_data):
    """Helper function to write data to file"""
    with open("data.json", "w", encoding="utf-8") as _f:
        _f.write(json.dumps(_data))


def update_data():
    """Main function that follows the output of a `log stream` command with
    custom filters that check for hints that a camera or microphone has been
    activated or deactivated. Results are then stored in a json file.
    """
    cmd = [
        "log",
        "stream",
        "--predicate",
        '(subsystem contains "com.apple.UVCExtension" and composedMessage contains "Post PowerLog") || eventMessage contains "Post event kCameraStream" || composedMessage contains "numRunningAudioEngines"',
    ]

    with subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    ) as stream:
        builtin_camera = False
        previous_microphone_state = ""
        previous_camera_state = ""
        usb_camera = False
        microphone = False

        data = {"camActive": False, "micActive": False}

        for _l in stream.stdout:
            line = _l.decode("utf-8").rstrip()

            # Microphone
            if "numRunningAudioEngines =" in line:
                try:
                    microphone = bool(int(line[-1]) > 0)
                    # if int(line[-1]) > 0:
                    #    microphone = True
                    # else:
                    #    microphone = False
                except ValueError:
                    continue
                if microphone:
                    microphone_state = "active"
                    data["micActive"] = True
                else:
                    microphone_state = "not active"
                    data["micActive"] = False

                if microphone_state is not previous_microphone_state:
                    if DEBUG:
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
                if DEBUG:
                    print(f"Camera is {camera_state}")
                write_file(data)
                previous_camera_state = camera_state


update_thread = threading.Thread(target=update_data)
update_thread.start()

if __name__ == "__main__":
    app.run(host="192.168.10.10", port=8000, debug=DEBUG)
