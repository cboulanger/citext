#!/usr/bin/env python3
import re, sys, time, os, json, traceback, socket, errno
import sqlite3
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from configs import *

# a random integer id for the channel for which this process acts as a SSE backend
channel_id = os.environ.get('QUERY_STRING')

# SSE protocol output
sys.stdout.write('Cache-Control: no-store\n')
sys.stdout.write('Content-type: text/event-stream\n\n')

# connect to SQLite database
sock_conn = sqlite3.connect('tmp/ports.db')
cursor = sock_conn.cursor()

# create table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS channels
    (id INTEGER PRIMARY KEY, port INTEGER NOT NULL, last_action TIMESTAMP NOT NULL);
''')

# bind to new socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(('', 0))
port = sock.getsockname()[1]
sock.listen(5)

# save associated port in the sqlite3 database so that the port is
# discoverable by other processes that know the channel id

# check if the channel_id already exists
cursor.execute('SELECT * FROM channels WHERE id=?', (channel_id,))
row = cursor.fetchone()

# insert or update the port and the last_action timestamp in the database
if row is None:
    cursor.execute('''
        INSERT INTO channels(id, port, last_action)
        VALUES (?, ?, ?);
    ''', (channel_id, port, datetime.now()))
else:
    cursor.execute('''
        UPDATE channels
        SET port = ?, last_action = ?
        WHERE id = ?;
    ''', (port, datetime.now(), channel_id))

# commit changes
sock_conn.commit()

# terminate processes which haven't been used in more than an hour
one_hour_ago = datetime.now() - timedelta(hours=1)
cursor.execute('SELECT port FROM channels WHERE last_action < ?', (one_hour_ago,))
rows = cursor.fetchall()
for row in rows:
    event_json = json.dumps({
        "name": "sse_terminate",
        "data": ""
    })
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect(('', row[0]))
        client.send(bytes(event_json, 'utf-8'))
    finally:
        client.close()

sock_conn.close()

# log output
sys.stderr.write(f"SSE: Connected channel id {channel_id} with port {port}\n")
sys.stdout.write(f"event:debug\ndata:Server connected with channel id {channel_id}\n\n")
sys.stdout.flush()

# start infinite loop that listens for incoming messages on the given port
while True:
    sock_conn, addr = sock.accept()
    try:
        from_client = ''
        while True:
            data = sock_conn.recv(4096).decode()
            if not data: break
            from_client += data
        evt = json.loads(from_client)
        event_name = evt['name']
        event_data = evt['data']
        # Terminate process when receiving the "sse_terminate" event
        if event_name == "sse_terminate":
            # remove entry in database
            sql_conn = sqlite3.connect('tmp/ports.db')
            cursor = sql_conn.cursor()
            cursor.execute('DELETE FROM channels WHERE id = ?', (channel_id,))
            sql_conn.commit()
            sql_conn.close()
            # close port listener
            sock_conn.close()
            message = f"SSE: Shutting down process for channel #{channel_id}.\n"
            sys.stderr.write(message)
            sys.exit(0)
        # pass event data to client
        sys.stdout.write(f"event:{event_name}\ndata:{event_data}\n\n")
        sys.stdout.flush()

    except Exception as err:
        tb = traceback.format_exc()
        sys.stderr.write(tb)
        sys.stdout.write(f"event:error\ndata:{channel_id}:{str(err)}\n\n")
        sys.stdout.flush()

    finally:
        sock_conn.close()
