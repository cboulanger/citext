#!/usr/bin/env python3

import sys,os, cgi, traceback
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.utils import push_event
from commands.split import split_model
from commands.model_list import list_models
from commands.model_delete import delete_model_folders

params = cgi.parse()
channel_id = params['id'][0]
model_name = params['model_name'][0]

try:
    split_model_name = f"test_{model_name}"
    if split_model_name in list_models():
        delete_model_folders(split_model_name)
    # split into training and test data
    split_model(model_name, split_model_name)
    response = f"Model {model_name} was tested as {split_model_name}"
    push_event(channel_id, "info", success_msg)
except Exception as err:
    push_event(channel_id, "danger", str(err))
    tb = traceback.format_exc()
    sys.stderr.write(tb)
    response = tb
finally:
    print("Content-Type: text/plain\n")
    print(response)

