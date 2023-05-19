import json
import os, sys, subprocess, re, builtins
import socket
from configs import *
import sqlite3

class SSE:
    def __init__(self, channel_id):
        self.channel_id = channel_id

        # find out which internal port this channel id is associated with
        conn = sqlite3.connect('tmp/ports.db')
        cursor = conn.cursor()

        # Retrieve port for a given channel_id
        cursor.execute('SELECT port FROM channels WHERE id=?', (channel_id,))
        port_tuple = cursor.fetchone()
        if port_tuple is not None:
            port = port_tuple[0]
        else:
            raise RuntimeError(f"No port exists for channel id {channel_id}")

        self.port = port
        conn.close()


    def push_event(self, event_name: str, event_data: str = ""):

        # sys.stderr.write(f"Connecting to channel {channel_id} via port {str(port)}...\n")
        event_json = json.dumps({
            "name": event_name,
            "data": event_data
        })
        # sys.stderr.write(f"To client: {event_json}\n")
        # connect to event server and send event
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('', self.port))
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
