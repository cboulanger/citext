#!/usr/bin/env python3

# todo: make server multi-threaded: https://stackoverflow.com/a/46224191

from http.server import HTTPServer, CGIHTTPRequestHandler, test
import sys

class CORSRequestHandler (CGIHTTPRequestHandler):
    def end_headers (self):
        self.send_header('Access-Control-Allow-Origin', '*')
        CGIHTTPRequestHandler.end_headers(self)

if __name__ == '__main__':
    test(CORSRequestHandler, HTTPServer, port=int(sys.argv[1]) if len(sys.argv) > 1 else 8000)
