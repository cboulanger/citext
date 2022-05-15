#!/usr/bin/env python3
import sys, os, cgi, traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.utils import push_event, redirectPrintToEvent
from configs import *
from commands.eval_full_workflow import run_full_eval_workflow

params = cgi.parse()
channel_id = params['id'][0]
model_name = params['model_name'][0]
skip_splitting = 'skip_splitting' in params
skip_segmentation = 'skip_segmentation' in params
skip_extraction = 'skip_extraction' in params

title = f"Evaluating model '{model_name}'"
oldprint = redirectPrintToEvent(channel_id, title)
response = f"{model_name}: Model evaluation results in the following accuracy values:"

try:
    extr_accuracy, seg_accuracy = run_full_eval_workflow(model_name, skip_splitting, skip_extraction, skip_segmentation)
    response += f" extraction: {extr_accuracy}"
    response += f" segmentation: {seg_accuracy}"
    push_event(channel_id, "success", response)
except Exception as err:
    push_event(channel_id, "error", str(err))
    tb = traceback.format_exc()
    sys.stderr.write(tb)
    response = tb
finally:
    push_event(channel_id, "info", title + ":")
    oldprint("Content-Type: text/plain\n")
    oldprint(response)
