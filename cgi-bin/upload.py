#!/usr/bin/python3

import sys, os, cgi, tempfile
print("Content-type: application/json")
print()

try:
    if not os.environ['CONTENT_LENGTH']:
        raise RuntimeError("No data")

    form = cgi.FieldStorage()

    if not "file" in form:
        raise RuntimeError("No form data")

    fileitem = form['file']
    filename = fileitem.filename
    tmpdir = tempfile.gettempdir()
    filepath = tmpdir + "/" + filename

    open(filepath, 'wb').write(fileitem.file.read())

    print('{"id":"' + filename + '"}')

except RuntimeError as err:
    print('{"error":"'+str(err)+'"}')
