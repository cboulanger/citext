#!/usr/bin/env python3
import re
import sys, time, os, json, traceback
import socket, errno

channel_id = os.environ.get('QUERY_STRING')

sys.stdout.write('Cache-Control: no-store\n')
sys.stdout.write('Content-type: text/event-stream\n\n')

# cleanup channel_id -> port cache
for file_name in os.listdir("tmp"):
    if not re.match("^[\d]+$", file_name): continue
    file_path = os.path.join("tmp", file_name)
    with open(file_path) as f:
        port = int(f.read())
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind(('', port))
            os.remove(file_path)
        except socket.error as e:
            if e.errno != errno.EADDRINUSE:
                pass
            else:
                print(e)
        s.close()

# bind to new socket and save associated port
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(('', 0))
port = sock.getsockname()[1]
sock.listen(5)
with open(f"tmp/{channel_id}", "w") as f:
    f.write(str(port))

sys.stderr.write(f"SSE: Connected channel id {channel_id} with port {port}\n")
sys.stdout.write(f"event:success\ndata:Server connected\n\n")
sys.stdout.flush()

while True:
    conn, addr = sock.accept()
    try:
        from_client = ''
        while True:
            data = conn.recv(4096).decode()
            if not data: break
            #sys.stderr.write(f"Received as str: {data}\n")
            from_client += data
        evt = json.loads(from_client)
        event_name = evt['name']
        event_data = evt['data']
        sys.stdout.write(f"event:{event_name}\ndata:{event_data}\n\n")
        sys.stdout.flush()

    except Exception as err:
        tb = traceback.format_exc()
        sys.stderr.write(tb)
        sys.stdout.write(f"event:error\ndata:{channel_id}:{str(err)}\n\n")
        sys.stdout.flush()

    finally:
        conn.close()

