import json
import os, sys, subprocess, re, builtins
import socket
from configs import *
from lib.logger import log

def get_message_path(channel_id) -> str:
    if not channel_id:
        raise ValueError("Missing channel id")
    return os.path.join(config_tmp_dir(), channel_id)


def get_lock_path(channel_id) -> str:
    if not channel_id:
        raise ValueError("Missing channel id")
    return os.path.join(config_tmp_dir(), channel_id + ".lock")


def push_event(channel_id, event_name: str, event_data: str):
    # find out which internal port this channel id is associated with
    file_path = os.path.join(config_tmp_dir(), str(channel_id))
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


def redirectPrintToEvent(channel_id, msg_prefix):
    oldprint = builtins.print
    #sys.stdout = StdoutToEvent(channel_id)

    def print2event(*args, sep=' ', end='\n', file=None):
        message = sep.join(args)
        if message.strip("\n"):
            if "RuntimeWarning" not in message:
                # remove control characters
                message_clean = re.sub("[\x00-\x1f\x7f-\x9f]", "", message)
                if message_clean.strip() and "[?" not in message_clean: # ugly workaround
                    push_event(channel_id, "info", f"{msg_prefix}: {message_clean}")
            sys.stderr.write(message + end)
            sys.stderr.flush()
        # piggybacking to allow aborting
        checkForAbortSignal(channel_id)

    builtins.print = print2event
    return oldprint


import threading

class InvervalJob(threading.Thread):
    def __init__(self, callback, event, interval):
        '''runs the callback function after interval seconds
        :param callback:  callback function to invoke
        :param event: external event for controlling the update operation
        :param interval: time in seconds after which are required to fire the callback
        :type callback: function
        :type interval: int
        '''
        self.callback = callback
        self.event = event
        self.interval = interval
        super(InvervalJob,self).__init__()

    def run(self):
        while not self.event.wait(self.interval):
            self.callback()

def getAbortSignalPath(channel_id):
    return os.path.join(config_tmp_dir(), channel_id + '.abort')

def setAbortSignal(channel_id):
    if not os.path.exists(os.path.join(config_tmp_dir(), channel_id)):
        raise ValueError(f"Invalid channel id {channel_id}")
    with open(getAbortSignalPath(channel_id), "w") as f:
        f.write("cancel")

def checkForAbortSignal(channel_id):
    abort_signal_path = getAbortSignalPath(channel_id)
    if os.path.exists(abort_signal_path):
        os.remove(abort_signal_path)
        raise InterruptedError("Canceled")

def run_command(command) -> str:
    msg = f">>> Executing '{command}'\n"
    log(msg)
    proc = subprocess.Popen([command], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, shell=True)
    lines = []
    while True:
        return_code = proc.poll()
        if return_code is not None:
            break
        line = str(proc.stdout.readline()).strip()
        if line != "":
            log(line)
            lines.append(line)

    # subprocess returned with error
    if return_code != 0:
        lines = [line.strip('\n') for line in proc.stderr.readlines() if line.strip('\n')]
        err_msg = '\n'.join(lines)
        raise RuntimeError(err_msg)

    return "\n".join(lines)

def increment_file_version(file_path):
    file_info_path = file_path + ".info"
    if os.path.exists(file_info_path):
        with open(file_info_path) as f:
            file_info = json.load(f)
        file_version = file_info['version'] if 'version' in file_info.keys() else 0
    else:
        file_version = 0
    file_info = {
        "modified": os.path.getmtime(file_path),
        "version": file_version + 1
    }
    with open(file_info_path, "w", encoding="utf-8") as f:
        json.dump(file_info, f)
