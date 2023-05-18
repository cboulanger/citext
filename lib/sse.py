import json
import os, sys, subprocess, re, builtins
import socket
from configs import *
from lib.logger import log

class SSE:
    def __init__(self, channel_id):
        self.channel_id = channel_id

    def push_event(self, event_name: str, event_data: str = ""):
        # find out which internal port this channel id is associated with
        file_path = os.path.join(config_tmp_dir(), str(self.channel_id))
        with open(file_path) as f:
            port = int(f.read())
        # sys.stderr.write(f"Connecting to channel {channel_id} via port {str(port)}...\n")
        event_json = json.dumps({
            "name": event_name,
            "data": event_data
        })
        # sys.stderr.write(f"To client: {event_json}\n")
        # connect to event server and send event
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('', port))
        client.send(bytes(event_json, 'utf-8'))
        client.close()
        return True

class Toast:
    def __init__(self, sse:SSE, type: str, title:str|None):
        match type:
            case 'success' | 'info' | 'warning' | 'error':
                self.type = type
                self.title = title or type.capitalize()
                self.sse = sse
                return
        raise f"Invalid type {type}"

    def show(self, message:str):
        self.sse.push_event(self.type, f"{self.title}:{message}")

    def close(self):
        self.sse.push_event(self.type, f"{self.title}:")
