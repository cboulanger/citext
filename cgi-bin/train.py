#!/usr/bin/env python3

import sys, os, time, cgi, builtins, traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.utils import push_event, redirectPrintToEvent
from commands.training import *

params = cgi.parse()
channel_id = params['id'][0]
model_name = params['model_name'][0]

title = f"Training model '{model_name}'"
oldprint = redirectPrintToEvent(channel_id, title)

try:
    st = time.time()
    call_extraction_training(model_name)
    call_segmentation_training(model_name)
    call_completeness_training(model_name)
    et = time.time()
    elapsed_time = int(et - st)
    response = f"Finished training of '{model_name}' in {elapsed_time} s ..."
    push_event(channel_id, "success", response)
except Exception as err:
    push_event(channel_id, "error", str(err))
    response = traceback.format_exc()
    sys.stderr.write(response)
finally:
    push_event(channel_id, "info", title + ":")
    oldprint("Content-Type: text/plain\n")
    oldprint(response)
