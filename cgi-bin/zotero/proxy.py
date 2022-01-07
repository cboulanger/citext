#!/usr/bin/python3
# This script works around the CORS restrictions of the zotero server on localhost

import sys, os, json, requests, socket

request_method = os.environ.get('REQUEST_METHOD')
content_length = os.environ.get('CONTENT_LENGTH')
endpoint = os.environ.get('QUERY_STRING')

zotero_connector_url = "http://127.0.0.1:23119/"
endpoint_url = zotero_connector_url + endpoint

os.environ['no_proxy'] = '127.0.0.1,localhost'

try:
    if request_method == "GET":
        response = requests.get(endpoint_url )

    elif request_method == "POST":
        # get post data
        payload = ""
        if content_length != "" and int(content_length) > 0:
            payload = sys.stdin.readline()
        response = requests.post(url=endpoint_url, data=payload)
    else:
        print("Status: 405 Method Not Allowed")
        print()
        print("Method" + request_method + " is not supported.")
        sys.exit(0)

    print("Status: " + str(response.status_code))
    print("Content-type: " + response.headers.get("content-type"))
    print()
    print(response.text)

except requests.exceptions.ConnectionError as err:
    print("Content-Type: text/plain")
    print()
    print("No connection at " + endpoint_url + ": " + str(err))
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print(local_ip)
except BaseException as err:
    print("Content-Type: text/plain")
    print()
    print(str(err))
