#!/usr/bin/env python3
# This script works around the CORS restrictions of the zotero server on localhost

import sys, os, requests

content_length = os.environ.get('CONTENT_LENGTH')
query_string = os.environ.get('QUERY_STRING')

zotero_connector_url = "http://127.0.0.1:23119/"

try:
    if content_length == "" or int(content_length) == 0:
        raise RuntimeError("No data");
    payload = sys.stdin.readline()
    response = requests.post(url=endpoint_url, data=payload)


    print("Status: " + str(response.status_code))
    print("Content-type: " + response.headers.get("content-type"))
    print()
    print(response.text)

except BaseException as err:
    print("Status: 500 Internal Server Error")
    print()
    print(str(err))
