#!/usr/bin/python3

# for debugging only
import cgitb
cgitb.enable();
#print("Content-type: text/html")

import sys, io, json, os, cgi
print("Content-type: application/json")
print()

form = cgi.FieldStorage()
filename = str(form.getvalue("filename"))

if filename == "None":
    print('{"error":"No filename given"}')
    sys.exit(0)

filepath = os.getcwd() + "/Data/3-refs_seg/" + filename

try:
    file = io.open(filepath + "/" + filename, mode="r", encoding="utf-8")
    data = file.read()
    file.close()
except FileNotFoundError:
    print('{"error":"' + filepath + ' does not exist"}')
    sys.exit(0)

print('{"refs_seg":' + json.dumps(data) + '}')
