#!/usr/bin/python3

import sys, json, os

print("Content-type: application/json")
print()

try:
    contLen = int(os.environ['CONTENT_LENGTH'])

    if contLen == 0:
        raise RuntimeError("No data")

    payload = sys.stdin.readline()

    payload = json.loads(payload)
    data_type = payload["type"]
    data = payload["data"]
    filename = payload["filename"]

    if filename == "":
        raise RuntimeError("No filename given")

    filepath = os.getcwd() + "/Exparser/Dataset/"

    if data_type == "layout":
        filepath += "LRT"
    elif data_type == "ref_xml":
        filepath += "SEG"
    else:
        raise RuntimeError("Invalid type")

    data = data.encode("utf8")
    file = open(filepath + "/" + filename, "wb")
    file.write(data)
    file.close()

    print('{"status":"OK"}')

except RuntimeError as err:
    print('{"error":"'+str(err)+'"}')

