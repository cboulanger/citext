#!/usr/bin/env python3

import sys, datetime, time, os
from utils import pull_event

channel_id = os.environ.get('QUERY_STRING')

try:
    sys.stdout.write('Cache-Control: no-store\n')
    sys.stdout.write('Content-type: text/event-stream\n\n')

    while True:
        event_message = pull_event(channel_id)
        if event_message != "":
            sys.stdout.write(f"{event_message}\n\n")
            sys.stdout.flush()
        time.sleep(0.5)

except Exception as err:
    sys.stdout.write('Status: 403 Bad Request \n')
    sys.stdout.write('Content-type: text/plain\n\n')
    sys.stdout.write(str(err) + "\n")
    sys.stderr.write(str(err) + "\n")
