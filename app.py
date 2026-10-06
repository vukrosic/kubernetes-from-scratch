"""The workload: a tiny web server. Kubernetes calls one running copy a pod.

    python3 app.py web-1 18101 v1

GET /        -> "hello from web-1 (v1)"
GET /health  -> "ok"
GET /freeze  -> from now on the program hangs: alive, but it never answers
GET /crash   -> the program dies on the spot
"""
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

name, port, version = sys.argv[1], int(sys.argv[2]), sys.argv[3]
frozen = False


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        global frozen
        if self.path == '/crash':
            os._exit(1)
        if self.path == '/freeze':
            frozen = True
        if frozen:
            time.sleep(3600)
        body = b'ok' if self.path == '/health' else f'hello from {name} ({version})'.encode()
        self.send_response(200)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


if version.endswith('broken'):      # a bad release: it crashes the moment it starts
    sys.exit(1)
time.sleep(0.25)                    # a real program loads things first: it runs, but it cannot answer yet
ThreadingHTTPServer.request_queue_size = 128            # many callers may wait in line
ThreadingHTTPServer.handle_error = lambda *args: None    # a caller that died half way is not an error
ThreadingHTTPServer(('127.0.0.1', port), Handler).serve_forever()
