#!/usr/bin/env python3

import json
import logging
import re
import subprocess
import sys
import time
from flask import Flask, jsonify
from multiprocessing import Process, Queue, Lock


DATA_FILE_PATH = "data.json"
DATA_LOCK = Lock()

app = Flask(__name__)

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


class CommandStreamReader:
    def __init__(self, cmd, queue, _type):
        self.process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        self.queue = queue
        self._type = _type

    def stream_output(self):
        while True:
            output = self.process.stdout.readline().decode("utf-8").strip()
            if output == "" and self.process.poll() is not None:
                break
            self.queue.put({"type": self._type, "data": output})
            self.queue.put({"type": self._type, "data": ""})  # clear the buffer


class StateManager:
    def __init__(self, data_file_path, lock):
        self.data_file_path = data_file_path
        self.lock = lock
        self.states = {
            "camActive": False,
            "webrtcMicActive": False,
            "systemMicActive": False,
            "micActive": False,
        }
        self.last_states = {
            "camActive": None,
            "webrtcMicActive": None,
            "systemMicActive": False,
            "micActive": False,
        }
        self.load_state()

    def load_state(self):
        try:
            with open(self.data_file_path, "r", encoding="utf-8") as f:
                self.states = json.load(f)
        except FileNotFoundError:
            pass  # No previous state file

    def save_state(self):
        with self.lock:
            with open(self.data_file_path, "w", encoding="utf-8") as f:
                json.dump(self.states, f)

    def update_cam_state(self, new_state):
        if self.states["camActive"] != new_state:
            logging.info(f"Camera is {'not ' if not new_state else ''}active")
            self.states["camActive"] = new_state
            self.save_state()
        self.last_states["camActive"] = new_state

    def update_mic_state(self, system, webrtc):
        if system is not None:
            self.update_system_mic_state(system)
        if webrtc is not None:
            self.update_webrtc_mic_state(webrtc)

        new_state = self.states["micActive"]
        if not self.states["systemMicActive"]:
            new_state = False
        if self.states["webrtcMicActive"]:
            new_state = True

        if self.last_states["micActive"] != new_state:
            self.states["micActive"] = new_state
            logging.info(f"Mic is {'active' if new_state else 'not active'}")
            self.save_state()

        self.last_states["micActive"] = self.states["micActive"]

    def update_system_mic_state(self, new_state):
        if self.states["systemMicActive"] != new_state:
            logging.info(f"Mic (system) is {'active' if new_state else 'not active'}")
            self.states["systemMicActive"] = new_state
            self.save_state()
        self.last_states["systemMicActive"] = new_state

    def update_webrtc_mic_state(self, new_state):
        if self.states["webrtcMicActive"] != new_state:
            logging.info(f"Mic (webrtc) is {'active' if new_state else 'not active'}")
            self.states["webrtcMicActive"] = new_state
            self.save_state()
        self.last_states["webrtcMicActive"] = new_state


class SystemMicMonitor:
    def __init__(self, state_manager):
        self.state_manager = state_manager
        self.system_mic_active_clients = set()

    def process_log_data(self, data):
        if "PublishRecordingClientInfo: Report client" in data:
            parts = data.split()
            client_id = parts[parts.index("client") + 1]
            running_state = parts[parts.index("running:") + 1]
            if running_state == "yes":
                self.system_mic_active_clients.add(client_id)
            elif running_state == "no":
                try:
                    self.system_mic_active_clients.remove(client_id)
                except KeyError:
                    logging.error("Key not found")
            self.state_manager.update_mic_state(
                bool(len(self.system_mic_active_clients) > 0), None
            )


class WebRTCMicMonitor:
    def __init__(self, state_manager):
        self.state_manager = state_manager
        self.enabled_ids = []
        self.media_stream_ids = []
        self.last_len_enabled_ids = 0
        self.last_len_media_stream_ids = 0

        self.mic_active = False
        self.mic_last_state = False

        self.state_change = time.monotonic()

    def extract_id(self, string):
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

    def process_log_data(self, data):
        _id = self.extract_id(data)

        if "MediaStreamTrackImpl() [kind: audio" in data and "remote=false" in data:
            if len(self.enabled_ids) == 0:
                self.media_stream_ids.append(_id)
                logging.debug("New media stream ID: %s", _id)
                self.state_change = time.monotonic()
        if "setEnabled({enabled=true}) [kind: audio" in data:
            self.enabled_ids.append(_id)
            logging.debug("Audio track enabled: %s", _id)
            self.state_change = time.monotonic()
        if "setEnabled({enabled=false}) [kind: audio" in data:
            if len(self.media_stream_ids) > 0:
                self.enabled_ids = [
                    x for x in self.enabled_ids if x not in self.media_stream_ids
                ]
                self.media_stream_ids = []
            try:
                self.enabled_ids.remove(_id)
                self.state_change = time.monotonic()
            except ValueError:
                logging.debug("Failed to remove ID: %s", _id)

        # Check if the lengths of the lists have changed
        if (
            len(self.media_stream_ids) != self.last_len_media_stream_ids
            or len(self.enabled_ids) != self.last_len_enabled_ids
        ):
            logging.debug(
                f"Media stream or enabled IDs changed {len(self.media_stream_ids)} {len(self.enabled_ids)}"
            )
            self.last_len_media_stream_ids = len(self.media_stream_ids)
            self.last_len_enabled_ids = len(self.enabled_ids)

        if time.monotonic() - self.state_change > 0.1:
            if len(self.media_stream_ids) > 0 or len(self.enabled_ids) > 0:
                self.mic_active = True
            else:
                self.mic_active = False

        state_manager.update_mic_state(None, self.mic_active)


class CameraMonitor:
    def __init__(self, state_manager):
        self.state_manager = state_manager

    def process_log_data(self, data):
        if "kCameraStreamStart" in data or '"VDCAssistant_Power_State" = On;' in data:
            logging.debug("Camera saw on")
            self.state_manager.update_cam_state(True)
        elif "kCameraStreamStop" in data or '"VDCAssistant_Power_State" = Off;' in data:
            logging.debug("Camera saw off")
            self.state_manager.update_cam_state(False)


def stream_command(command, queue, _type):
    stream_reader = CommandStreamReader(command, queue, _type)
    stream_reader.stream_output()


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
        _data = {
            "camActive": False,
            "systemMicActive": False,
            "webrtcMicActive": False,
            "micActive": False,
        }
    return jsonify(_data)


def start_flask_app():
    app.run(host="192.168.10.10", port=8000, debug=True, use_reloader=False)


if __name__ == "__main__":
    flask_thread = Process(target=start_flask_app)
    flask_thread.start()

    if len(sys.argv) > 1 and sys.argv[1] == "-v":
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    logging.basicConfig(level=log_level)

    state_manager = StateManager(DATA_FILE_PATH, DATA_LOCK)
    system_mic_monitor = SystemMicMonitor(state_manager)
    webrtc_mic_monitor = WebRTCMicMonitor(state_manager)
    cam_monitor = CameraMonitor(state_manager)

    queue = Queue()

    stream_log_thread = Process(
        target=stream_command,
        args=(
            log_stream_cmd,
            queue,
            "log",
        ),
    )
    stream_log_thread.start()
    chrome_thread = Process(
        target=stream_command,
        args=(
            chrome_debug_cmd,
            queue,
            "chrome",
        ),
    )
    chrome_thread.start()

    while True:
        log = False
        chrome = False
        data = queue.get().get("data", "")
        _type = queue.get().get("type", "")
        if _type == "chrome":
            webrtc_mic_monitor.process_log_data(data)
        elif _type == "log":
            cam_monitor.process_log_data(data)
            system_mic_monitor.process_log_data(data)
