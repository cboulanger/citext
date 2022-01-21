#!/usr/bin/env python3
# This script works around the CORS restrictions of the zotero server on localhost

import sys, os, requests

request_method = os.environ.get('REQUEST_METHOD')
content_length = os.environ.get('CONTENT_LENGTH')
content_type = os.environ.get('CONTENT_TYPE')
endpoint = os.environ.get('QUERY_STRING')

zotero_connector_url = "http://127.0.0.1:23119/"
endpoint_url = zotero_connector_url + endpoint

os.environ['no_proxy'] = '127.0.0.1,localhost'

try:
    if request_method == "GET":
        response = requests.get(endpoint_url, timeout=10)
    elif request_method == "POST":
        payload = ""
        if content_length != "" and int(content_length) > 0:
            payload = sys.stdin.read(int(content_length))
        response = requests.post(url=endpoint_url, data=payload, headers={
            "Content-type": content_type
        })
    else:
        print("Status: 405 Method Not Allowed")
        print()
        print("Method" + request_method + " is not supported.")
        sys.exit(0)

    print("Status: " + str(response.status_code))
    print("Content-type: " + response.headers.get("content-type"))
    print()
    print(response.text)

except BaseException as err:
    print("Status: 500 Internal Server Error")
    print()
    print(str(err))
