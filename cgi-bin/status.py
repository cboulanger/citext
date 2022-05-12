#!/usr/bin/env python3
import os, json, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from configs import *

print("Content-type: application/json")
print()

# existing models
model_names = []
for dirname in os.listdir(config_dataset_dir()):
    path = os.path.join(config_dataset_dir(), dirname)
    if os.path.isdir(path) and not dirname.startswith("test_"):
        model_names.append(dirname)
result = {'model_names': model_names}
print(json.dumps(result))
