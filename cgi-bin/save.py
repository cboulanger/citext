#!/usr/bin/python3

import sys
import json
import os

print ("Content-type: application/json\n")

try:
    payload = sys.stdin.read()
    try:
        payload = json.loads(payload)
    except:
        print ('{"error":"Invalid JSON data"}')
        sys.exit()

    type = payload["type"]
    data = payload["data"]

    filename = payload["filename"]
    filepath = os.getcwd() + "/../Exparser/Dataset/"

    if type == "layout":
        filepath += "LRT"
    elif type == "ref_xml":
        filepath += "SEG"
    else:
        print ('{"error":"Invalid type"}')
        sys.exit()

    data = data.encode("utf8")
    file = open(filepath + "/" + filename, "wb")
    file.write(data)
    file.close()

    print ('{"status":"OK"}')

except Exception as err:
    print ('{"error":"' + str(err) + ' in line ' +  str(err.__traceback__.tb_lineno) + '"}')

