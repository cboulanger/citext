#!/usr/bin/env python3
import json, cgi, shutil,  sys, tempfile, urllib.request, os

form = cgi.FieldStorage()
url = form.getvalue("url")
tmpdir = None

try:
    if not url:
        raise RuntimeError("No URL given")

    filename = url.split("/").pop()
    match url.split(":"):
        case ['file', filepath]:
            if filepath.startswith('/zotero-storage') or filepath.startswith('Dataset'):
                if not os.path.isfile(filepath):
                    raise Exception(f"{filepath} does not exist.")
            else:
                raise Exception(f"Access forbidden for {filepath}")

        case ['http' | 'https']:
            tmpdir = tempfile.gettempdir()
            filepath = tmpdir + "/" + filename
            urllib.request.urlretrieve(url, filepath)

        case _:
            raise Exception("Invalid URL")

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

