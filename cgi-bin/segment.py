#!/usr/bin/python3

import sys
import io
import json
import os
import cgitb

print ("Content-type: application/json\n")

try:
    form = cgi.FieldStorage()
    filename = form.getValue("filename")

    if (filename == ""):
        print('{"error":"No filename given"}')
        sys.exit()

    filepath = os.getcwd() + "/../Data/3-refs_seg/" + filename

    file = io.open(filepath + "/" + filename, mode="r", encoding="utf-8")
    data = file.read()
    file.close()
    print ('{"refs_seg":' + json.dumps(data) + '}')

except Exception as err:
    print ('{"error":"' + str(err) + ' in line ' +  str(err.__traceback__.tb_lineno) + '"}')
