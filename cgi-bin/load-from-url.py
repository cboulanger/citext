#!/usr/bin/env python3
import json, cgi, shutil,  sys, tempfile, urllib.request, os

form = cgi.FieldStorage()
url = form.getvalue("url")

try:

    if not url:
        raise RuntimeError("No URL given")

    filename = url.rsplit('/', 1)[1]

    if url.startswith("file:/"):
        filepath = url[6:]
    else:
        tmpdir = tempfile.gettempdir()
        filepath = tmpdir + "/" + filename
        # download
        urllib.request.urlretrieve(url, filepath)

    print("Content-type: application/octet-stream")
    print("Content-Disposition: attachment; filename=%s" % filename)
    print()
    sys.stdout.flush()

    with open(filepath, 'rb') as file:
        shutil.copyfileobj(file, sys.stdout.buffer)

    if not url.startswith("file:/"):
        os.remove(filepath)

except BaseException as err:
    import traceback
    traceback.print_exc()
    result = {}
    result["error"] = str(err)
    print("Content-type: application/json")
    print()
    print(json.dumps(result))

