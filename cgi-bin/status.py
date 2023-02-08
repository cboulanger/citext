#!/usr/bin/env python3
import os, json, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from configs import *
from dotenv import load_dotenv
load_dotenv()

print("Content-type: application/json")
print()

# existing models
model_names = ['default']
model_dir = config_model_dir()
for dirname in os.listdir(model_dir):
    path = os.path.join(model_dir, dirname)
    if os.path.isdir(path) and not dirname.startswith("test_"):
        model_names.append(dirname)
model_names.sort(reverse=True)
result = {
    'webdav_storage': bool(os.environ.get("WEBDAV_HOST")),
    'model_names': model_names
}
print(json.dumps(result))
