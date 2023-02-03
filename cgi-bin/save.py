#!/usr/bin/env python3

import sys, json, os, shutil, re
import xml.dom.minidom
from datetime import datetime
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
    engine = payload["engine"]
    data = payload["data"]
    file_name = payload["filename"]
    model_name = payload["modelName"]

    if file_name == "":
        raise RuntimeError("No filename given")

    if model_name == "":
        raise RuntimeError("No model name given")

    dir_name = os.path.join(os.getcwd(), config_dataset_dir(), model_name, engine, data_type)
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

    # pretty-print xml
    if file_name.endswith(".xml"):
        data = xml.dom.minidom.parseString(data)
        data = data.toprettyxml(encoding="utf-8", indent="    ").decode("utf-8")
        data = re.sub("\n *\n", "\n", data)
        data = re.sub("\n *\n", "\n", data)

    file_path = os.path.join(dir_name, file_name)

    # backup existing files in tmp dir
    if os.path.exists(file_path):
        time_string = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_path = os.path.join("tmp", os.path.basename(file_path) + f".{time_string}.bak")
        shutil.move(file_path, backup_path)

    # save file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(data)

    # save sync info
    file_info_path = file_path + ".info"
    if os.path.exists(file_info_path):
        with open(file_info_path) as f:
            file_info = json.load(f)
    else:
        file_info = {
            "modified": 0,
            "version": 0
        }
    file_version = file_info['version'] if 'version' in file_info.keys() else 1
    file_info['version'] += 1
    file_info['modified'] = os.path.getmtime(file_path)
    with open(file_info_path, "w", encoding="utf-8") as f:
        json.dump(file_info, f)

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

