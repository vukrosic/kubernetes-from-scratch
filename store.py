"""The store: the one place where the wish and the facts are written down.

    python3 store.py        (listens on port 18000)

Every other program reads the store and writes to the store.
They never talk to each other directly.
"""
import json
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

URL = 'http://127.0.0.1:18000'


def call(request):
    """Send one request to the store. Try a few times before giving up."""
    for attempt in range(5):
        try:
            with urllib.request.urlopen(request, timeout=1) as reply:
                return reply.read()
        except OSError:
            time.sleep(0.02)
    return None


def read():
    """The whole state as one dictionary. None if the store does not answer."""
    reply = call(URL)
    return json.loads(reply) if reply else None


def write(path, value):
    """write(['pods', 'web-1', 'ready'], True)"""
    send({'path': path, 'value': value})


def erase(path):
    """erase(['pods', 'web-1'])"""
    send({'path': path})


def send(change):
    call(urllib.request.Request(URL, json.dumps(change).encode()))


STATE = {'want': 0, 'version': 'v1', 'made': 0, 'pods': {}, 'nodes': {}}
LOCK = threading.Lock()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        with LOCK:
            self.answer(json.dumps(STATE).encode())

    def do_POST(self):
        change = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        *folders, last = change['path']
        with LOCK:
            place = STATE
            for key in folders:
                place = place.get(key, {})      # a pod that was erased: the write goes nowhere
            if 'value' in change:
                place[last] = change['value']
            else:
                place.pop(last, None)
        self.answer(b'ok')

    def answer(self, body):
        self.send_response(200)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


if __name__ == '__main__':
    ThreadingHTTPServer.request_queue_size = 128        # many callers may wait in line
    ThreadingHTTPServer.handle_error = lambda *args: None    # a caller that died half way is not an error
    ThreadingHTTPServer(('127.0.0.1', 18000), Handler).serve_forever()
