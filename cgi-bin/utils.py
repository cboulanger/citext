import os, sys, subprocess, re


def get_message_path(channel_id) -> str:
    if not channel_id:
        raise ValueError("Missing channel id")
    return os.path.join("tmp", channel_id)


def get_lock_path(channel_id) -> str:
    if not channel_id:
        raise ValueError("Missing channel id")
    return os.path.join("tmp", channel_id + ".lock")


def push_event(channel_id, event_name: str, event_data: str):
    event_data = re.sub("[\x00-\x1f\x7f-\x9f]","",event_data)
    server_message = f"event: {event_name}\ndata: {event_data}\n\n"
    if os.path.exists(get_lock_path(channel_id)):
        sys.stderr.write(f"Lock for {channel_id} exists, not pushing event\n")
        return
    try:
        with open(get_lock_path(channel_id), "w") as l:
            l.write("locked")
        with open(get_message_path(channel_id), "w") as f:
            f.write(server_message)
    except Exception as err:
        sys.stderr.write(str(err) + "\n")
    finally:
        try:
            os.remove(get_lock_path(channel_id))
        except:
            pass


def pull_event(channel_id) -> str:
    if os.path.exists(get_lock_path(channel_id)):
        sys.stderr.write(f"Lock for {channel_id} exists, not pulling event\n")
        return ""
    if not os.path.exists(get_message_path(channel_id)):
        return ""
    try:
        with open(get_lock_path(channel_id), "w") as l:
            l.write("locked")
        with open(get_message_path(channel_id)) as f:
            server_message = f.read()
        return server_message
    except Exception as err:
        sys.stderr.write(str(err) + "\n")
        return ""
    finally:
        try:
            os.remove(get_message_path(channel_id))
            os.remove(get_lock_path(channel_id))
        except:
            pass


def run_command(channel_id, command, *params):
    # run docker command and write output to server output
    args = ['python3', '/app/run-main.py', command, *params]
    sys.stderr.write(f"Executing {' '.join(args)}\n")
    proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    i=0
    while True:
        return_code = proc.poll()
        sys.stderr.write(f'Polling {i}\n')
        i+=1
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
        sys.stderr.write(err_msg)
        push_event(channel_id, 'danger', lines[-1])

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
