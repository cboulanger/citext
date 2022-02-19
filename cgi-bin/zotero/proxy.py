#!/usr/bin/env python3
# This script works around the CORS restrictions of the zotero server on localhost

import sys, os, requests

request_method = os.environ.get('REQUEST_METHOD')
content_length = os.environ.get('CONTENT_LENGTH')
content_type = os.environ.get('CONTENT_TYPE')
endpoint = os.environ.get('QUERY_STRING')

docker_host = "host.docker.internal" # works for Windows & Mac
# docker_host = "172.17.0.1" # this is for linux hosts, but how to know when to use this?
zotero_connector_url = "http://" + docker_host + ":23119/"
endpoint_url = zotero_connector_url + endpoint

try:
    if request_method == "GET":
        response = requests.get(endpoint_url, timeout=10, headers={
            "Host": "localhost"
        })
    elif request_method == "POST":
        if content_length != "" and int(content_length) > 0:
            payload = sys.stdin.readline(int(content_length))
        else:
            raise RuntimeError("No data")
        print("===> " + str(payload), file=sys.stderr)
        response = requests.post(url=endpoint_url, data=payload.encode('utf-8'), headers={
            "Host": "localhost",
            "Content-type": content_type
        })
        print("<=== " + str(response.text), file=sys.stderr)
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
    print("Error: " + str(err), file=sys.stderr)
