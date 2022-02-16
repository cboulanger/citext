#!/usr/bin/env python3
import os, json

print("Content-type: application/json")
print()

# existing models
model_names = []
dataset_dir = 'EXparser/Dataset'
for dirname in os.listdir(dataset_dir):
    path = os.path.join(dataset_dir, dirname)
    if os.path.isdir(path):
        model_names.append(dirname)
result = {'model_names': model_names}
print(json.dumps(result))
