#!/usr/bin/env python3

import os, cgi, tempfile, json
print("Content-type: application/json")
print()

result = {}

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
