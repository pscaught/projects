#!/usr/bin/env python3
"""Monitor whether a camera or microphone is active on macOS"""

import json
import logging
import threading
import subprocess
from flask import Flask, jsonify

DATA_FILE_PATH="data.json"
DATA_LOCK = threading.Lock()
DEBUG = True

app = Flask(__name__)


@app.route("/")
def index():
    """Placeholder index.html"""
    return app.send_static_file("index.html")


@app.route("/data.json")
def get_data():
    """Read from json file and serve the contents at /data.json"""
    try:
        with open(DATA_FILE_PATH, "r", encoding="utf-8") as _f:
            _data = json.load(_f)
    except json.JSONDecodeError:
        _data = {"camActive": False, "micActive": False}
    return jsonify(_data)


def write_file(_data):
    """Helper function to write data to file"""
    with open(DATA_FILE_PATH, "w", encoding="utf-8") as _f:
        _f.write(json.dumps(_data))


def main():
    """Main function that follows the output of a `log stream` command with
    custom filters that check for hints that a camera or microphone has been
    activated or deactivated. Results are then stored in a json file.
    """
    logging.basicConfig(level=logging.DEBUG)
    cmd = [
        "log",
        "stream",
        "--predicate",
        '(subsystem contains "com.apple.UVCExtension" and composedMessage contains "Post PowerLog") || eventMessage contains "Post event kCameraStream" || composedMessage contains "PublishRecordingClientInfo: Report"',
    ]

    with subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    ) as stream:
        previous_cam_active_state = True
        previous_mic_active_state = True
        cam_active_state = False
        mic_active_state = False

        states = {"camActive": cam_active_state, "micActive": mic_active_state}

        for line in stream.stdout:
            line = line.decode("utf-8").rstrip()

            # Microphone
            if "PublishRecordingClientInfo: Report" in line:
                if 'yes' in line:
                    mic_active_state = True
                elif 'no' in line:
                    mic_active_state = False

                states["micActive"] = mic_active_state

            if mic_active_state != previous_mic_active_state:
                logging.debug(f"Microphone is {'active' if mic_active_state else 'not active'}")
                with DATA_LOCK:
                    write_file(states)
                previous_mic_active_state = mic_active_state

            # Camera
            if (
                "kCameraStreamStart" in line
                or '"VDCAssistant_Power_State" = On;' in line
            ):
                cam_active_state = True
            elif (
                "kCameraStreamStop" in line
                or '"VDCAssistant_Power_State" = Off;' in line
            ):
                cam_active_state = False

            states["camActive"] = cam_active_state

            if cam_active_state != previous_cam_active_state:
                logging.debug(f"Camera is {'active' if cam_active_state else 'not active'}")
                with DATA_LOCK:
                    write_file(states)
                previous_cam_active_state = cam_active_state


if __name__ == "__main__":
    # Start the Flask app in a separate thread
    flask_thread = threading.Thread(
        target=lambda: app.run(
            host="192.168.10.10", port=8000, debug=True, use_reloader=False
        ),
        daemon=True,
    )
    flask_thread.start()

    # Start the data processing in the main thread
    main()
