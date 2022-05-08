import json
import os, sys, subprocess, re
import socket


def get_message_path(channel_id) -> str:
    if not channel_id:
        raise ValueError("Missing channel id")
    return os.path.join("tmp", channel_id)


def get_lock_path(channel_id) -> str:
    if not channel_id:
        raise ValueError("Missing channel id")
    return os.path.join("tmp", channel_id + ".lock")


def push_event(channel_id, event_name: str, event_data: str):
    # find out which internal port this channel id is associated with
    file_path = os.path.join("tmp", str(channel_id))
    with open(file_path) as f:
        port = int(f.read())
    #sys.stderr.write(f"Connecting to channel {channel_id} via port {str(port)}...\n")
    # remove control characters
    event_data = re.sub("[\x00-\x1f\x7f-\x9f]","",event_data)
    event_json = json.dumps({
        "name": event_name,
        "data": event_data
    })
    # connect to event server and send event
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('', port))
    client.send(bytes(event_json, 'utf-8'))
    client.close()



def run_shell_command(channel_id, *args):
    # run shell command and write output to server output
    sys.stderr.write(f"Executing {' '.join(args)}\n")
    proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    while True:
        return_code = proc.poll()
        if return_code is not None:
            break
        line = proc.stdout.readline().strip()
        if line != "":
            # write to stderr so that it is printed in the server output
            sys.stderr.write(line + '\n')
            sys.stderr.flush()
            push_event(channel_id, 'info', line)

    # subprocess returned with error
    if return_code != 0:
        lines = [line.strip('\n') for line in proc.stderr.readlines() if line.strip('\n')]
        err_msg = '\n'.join(lines)
        sys.stderr.write(err_msg + "\n")
        raise RuntimeError(lines[-1] if len(lines) > 0 else "Unknown error")

class StdoutToEvent(object):
    def __init__(self, channel_id):
        self.channel_id = channel_id
        self.stderr = sys.stderr

    def flush(self):
        self.stderr.flush()

    def write(self, message):
        self.stderr.write(message)
        self.flush()
        if message.strip("\n"):
            push_event(self.channel_id, "info", message)
