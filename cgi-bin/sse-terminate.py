#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.sse import SSE
channel_id = os.environ.get('QUERY_STRING')
sse = SSE(channel_id)
sse.push_event("sse_terminate")
message = f"SSE: Terminating channel #{channel_id}.\n"
sys.stderr.write(message)
print("Content-Type: text/plain\n")
print(message)
