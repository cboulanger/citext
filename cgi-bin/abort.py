#!/usr/bin/env python3
import sys, os, cgi
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.utils import setAbortSignal
params = cgi.parse()
channel_id = params['id'][0]
setAbortSignal(channel_id)
print("Content-Type: text/plain\n")
print("OK")
