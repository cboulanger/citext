#!/usr/bin/env python3

import sys, json, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from configs import *

print("Content-type: application/json")
print()

result = {}

try:
    contLen = int(os.environ['CONTENT_LENGTH'])

    if contLen == 0:
        raise RuntimeError("No data")

    payload = sys.stdin.readline()

    payload = json.loads(payload)
    data_type = payload["type"]
    data = payload["data"]
    file_name = payload["filename"]
    model_name = payload["modelName"]

    if file_name == "":
        raise RuntimeError("No filename given")

    if model_name == "":
        raise RuntimeError("No model name given")

    dir_name = os.path.join(os.getcwd(), config_dataset_dir(), model_name)

    if data_type == "layout":
        dir_name = os.path.join(dir_name, "LRT")
    elif data_type == "ref_xml":
        dir_name = os.path.join(dir_name, "SEG")
    else:
        raise RuntimeError("Invalid type")

    data = data.encode("utf8")

    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

    file = open(os.path.join(dir_name, file_name), "wb")
    file.write(data)
    file.close()

    result["success"] = True

except RuntimeError as err:
    result["error"] = str(err)

except BaseException as err:
    import traceback
    traceback.print_exc()
    result["error"] = str(err)

finally:
    # return result
    print(json.dumps(result))

