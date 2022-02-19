#!/usr/bin/env python3
import json, cgi, shutil,  sys, tempfile, urllib.request, os

form = cgi.FieldStorage()
url = form.getvalue("url")
tmpdir = None

try:
    if not url:
        raise RuntimeError("No URL given")

    if url.startswith("file://zotero-storage/"):
        filepath = url[6:]
        filename = url.split("/").pop()
        if not os.path.isfile(filepath):
            raise Exception(filepath + " does not exist.")
    else:
        filename = url.rsplit('/', 1)[1]
        tmpdir = tempfile.gettempdir()
        filepath = tmpdir + "/" + filename
        urllib.request.urlretrieve(url, filepath)

    print("Content-type: application/octet-stream")
    print("Content-Disposition: attachment; filename=%s" % filename)
    print()
    sys.stdout.flush()

    with open(filepath, 'rb') as file:
        shutil.copyfileobj(file, sys.stdout.buffer)

    if tmpdir:
        os.remove(filepath)

except BaseException as err:
    import traceback
    traceback.print_exc()
    result = {}
    result["error"] = str(err)
    print("Content-type: application/json")
    print()
    print(json.dumps(result))

