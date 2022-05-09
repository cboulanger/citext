#!/usr/bin/env python3

import builtins
import sys,os, time, cgi
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.utils import push_event, redirectPrintToEvent
from commands.training import call_segmentation_training, call_extraction_training

params = cgi.parse()
channel_id = params['id'][0]
model_name = params['model_name'][0]

oldprint = redirectPrintToEvent(channel_id, f"Training model '{model_name}'")

try:
    st = time.time()
    call_extraction_training(model_name)
    call_segmentation_training(model_name)
    et = time.time()
    elapsed_time = int(et - st)
    response = f"Finished training of '{model_name}' in {elapsed_time} s ..."
    push_event(channel_id, "success", response)
except Exception as err:
    push_event(channel_id, "error", str(err))
    tb = traceback.format_exc()
    sys.stderr.write(tb)
    response = tb
finally:
    push_event(channel_id, "info", f"{model_name}:")
    oldprint("Content-Type: text/plain\n")
    oldprint(response)
