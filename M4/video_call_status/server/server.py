#!/usr/bin/env python3
"""Monitor whether a camera or microphone is active on macOS"""

import json
import logging
import re
import select
import subprocess
import time

# import threading
from flask import Flask, jsonify
from multiprocessing import Process, Lock

DATA_FILE_PATH = "data.json"
DATA_LOCK = Lock()
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


def start_flask_app():
    app.run(host="192.168.10.10", port=8000, debug=True, use_reloader=False)


def write_file(_data):
    """Helper function to write data to file"""
    with open(DATA_FILE_PATH, "w", encoding="utf-8") as _f:
        _f.write(json.dumps(_data))


def extract_id(string):
    """Extracts the ID from a string in the given format.

    Args:
        string: The input string.

    Returns:
        The extracted ID, or None if no ID was found.
    """

    match = re.search(r"id: (\w+-\w+-\w+-\w+-\w+)", string)
    if match:
        return match.group(1)
    else:
        return None


def main():
    """Main function that follows the output of a `log stream` command with
    custom filters that check for hints that a camera or microphone has been
    activated or deactivated. Results are then stored in a json file.
    """
    chrome_debug_cmd = [
        "tail",
        "-f",
        "/Users/scott/Library/Application Support/Google/Chrome/chrome_debug.log",
    ]
    log_stream_cmd = [
        "log",
        "stream",
        "--predicate",
        '(subsystem contains "com.apple.UVCExtension" and composedMessage contains "Post PowerLog") || eventMessage contains "Post event kCameraStream" || composedMessage contains "PublishRecordingClientInfo: Report"',
    ]

    # Merge the output of `log stream` and `tail -f chrome_debug.log` into a single stream
    with subprocess.Popen(
        log_stream_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    ) as log_stream, subprocess.Popen(
        chrome_debug_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    ) as chrome_debug_stream:

        # Definitive mic states
        mic_active = False
        mic_last_state = False

        #  `log stream` vars. We can see reliably whether the camera is in use.
        cam_active = False
        cam_last_state = False
        system_mic_active = False
        system_mic_active_clients = set()
        system_mic_last_state = False

        # 'chrome_debug.log' vars. We we can see if Chrome is using the Mic.
        enabled_ids = []
        media_stream_ids = []

        chrome_webrtc_mic_active = False
        chrome_webrtc_mic_last_state = False

        last_len_enabled_ids = 0
        last_len_media_stream_ids = 0

        state_change = 0 # used for debouncing changing state between active and inactive

        states = {"camActive": cam_active, "micActive": system_mic_active and chrome_webrtc_active}

        while True:
            # some interesting suggestion from Gemini to get both streams
            # to be readable for parsing
            readable, _, _ = select.select(
                [log_stream.stdout, chrome_debug_stream.stdout], [], []
            )

            for stream in readable:
                line = stream.readline().decode().rstrip()

                # System Microphone. Handle parsine to determine if the system
                # Mic is active.
                if "PublishRecordingClientInfo: Report client" in line:
                    parts = line.split()
                    client_id = parts[parts.index("client") + 1]
                    running_state = parts[parts.index("running:") + 1]

                    if running_state == "yes":
                        system_mic_active_clients.add(client_id)
                    elif running_state == "no":
                        try:
                            system_mic_active_clients.remove(client_id)
                        except KeyError:
                            logging.error("Key not found")
                    system_mic_active = bool(len(system_mic_active_clients) > 0)



                # Camera. Handle parsing to determine if the system camera
                # is enabled.
                if (
                    "kCameraStreamStart" in line
                    or '"VDCAssistant_Power_State" = On;' in line
                ):
                    cam_active = False
                elif (
                    "kCameraStreamStop" in line
                    or '"VDCAssistant_Power_State" = Off;' in line
                ):
                    cam_active = True

                states["camActive"] = cam_active

                if cam_active != cam_last_state:
                    logging.info(
                        f"Camera is {'active' if cam_active else 'not active'}"
                    )
                    with DATA_LOCK:
                        write_file(states)
                    cam_last_state = cam_active

                # Chrome WebRTC Microphone. Handle parsing to determine if
                # Chrome is using the Mic with WebRTC. (Meet and Teams)
                _id = extract_id(line)

                if (
                    "MediaStreamTrackImpl() [kind: audio" in line
                    and "remote=false" in line
                ):
                    if len(enabled_ids) == 0:
                        media_stream_ids.append(_id)
                        logging.debug("New media stream ID: %s", _id)
                        state_change = time.monotonic()
                if "setEnabled({enabled=true}) [kind: audio" in line:
                    enabled_ids.append(_id)
                    logging.debug("Audio track enabled: %s", _id)
                    state_change = time.monotonic()
                if "setEnabled({enabled=false}) [kind: audio" in line:
                    logging.debug("Audio track disabled: %s", _id)
                    state_change = time.monotonic()
                    if len(media_stream_ids) > 0:
                        enabled_ids = [
                            x for x in enabled_ids if x not in media_stream_ids
                        ]
                        media_stream_ids = []
                    try:
                        enabled_ids.remove(_id)
                    except ValueError:
                        logging.debug("Failed to remove ID: %s", _id)

                # Check if the lengths of the lists have changed
                if (
                    len(media_stream_ids) != last_len_media_stream_ids
                    or len(enabled_ids) != last_len_enabled_ids
                ):
                    logging.debug(
                        f"Media stream or enabled IDs changed {len(media_stream_ids)} {len(enabled_ids)}"
                    )
                    last_len_media_stream_ids = len(media_stream_ids)
                    last_len_enabled_ids = len(enabled_ids)

                if time.monotonic() - state_change > 0.2:
                    if len(media_stream_ids) > 0 or len(enabled_ids) > 0:
                        chrome_webrtc_mic_active = True
                    else:
                        chrome_webrtc_mic_active = False

                if chrome_webrtc_mic_active is not chrome_webrtc_mic_last_state:
                    logging.info(
                        "Mic active (webrtc)" if chrome_webrtc_mic_active else "Mic inactive (webrtc)"
                    )
                    chrome_webrtc_mic_last_state = chrome_webrtc_mic_active

                mic_active = system_mic_active and chrome_webrtc_mic_active


                if mic_active != mic_last_state:
                    states["micActive"] = mic_active
                    logging.info(
                        f"Microphone is {'active' if mic_active else 'not active'}"
                    )
                    with DATA_LOCK:
                        write_file(states)
                    mic_last_state = mic_active


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Start the Flask app in a separate thread
    flask_thread = Process(target=start_flask_app)
    flask_thread.start()

    # Start the data processing in the main thread
    main()
