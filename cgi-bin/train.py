#!/usr/bin/env python3

import builtins
import sys,os, time, cgi
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.utils import push_event, StdoutToEvent
from commands.training import call_segmentation_training, call_extraction_training

params = cgi.parse()
channel_id = params['id'][0]
model_name = params['model_name'][0]

oldstdout = sys.stdout
sys.stdout = StdoutToEvent(channel_id)

def print2event(*args, sep=' ', end='\n', file=None):
    message = sep.join(args)
    if message.strip("\n"):
        global channel_id
        global model_name
        push_event(channel_id, "info", f"{model_name}: {message}")
    sys.stderr.write(message + end)
    sys.stderr.flush()

builtins.print = print2event

st = time.time()
call_extraction_training(model_name)
call_segmentation_training(model_name)
et = time.time()
elapsed_time = int(et - st)

message = f"Finished training of '{model_name}' in {elapsed_time} s ..."
push_event(channel_id, "info", f"{model_name}:") # remove the info box
push_event(channel_id, "success", message)

oldstdout.write("Content-type: text/plain\n\n")
oldstdout.write(message)

