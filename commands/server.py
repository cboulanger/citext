import time, threading, socket
from http.server import HTTPServer, CGIHTTPRequestHandler, test

class CgiThread(threading.Thread):
    def __init__(self, i, addr, sock):
        threading.Thread.__init__(self)
        self.i = i
        self.addr = addr
        self.sock = sock
        self.daemon = True
        self.start()

    def run(self):
        httpd = HTTPServer(self.addr, CGIHTTPRequestHandler, False)
        # Prevent the HTTP server from re-binding every handler.
        # https://stackoverflow.com/questions/46210672/
        httpd.socket = self.sock
        httpd.server_bind = self.server_close = lambda self: None
        host, port = self.addr[:2]
        httpd.server_name = socket.getfqdn(host)
        httpd.server_port = port
        httpd.serve_forever()


# see https://stackoverflow.com/a/46224191
def server_start(port):
    # Create ONE socket.
    addr = ('0.0.0.0', port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(addr)
    sock.listen(5)
    # Create 10 handlers
    [CgiThread(i, addr, sock) for i in range(10)]
    print(f"Serving http and cgi requests from http://localhost:{port}")
    time.sleep(9e9)
