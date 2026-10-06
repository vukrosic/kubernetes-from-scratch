"""The service: one address that never changes, in front of pods that come and go.

    python3 service.py      (listens on port 18080)

For every request it reads the store, takes the pods that are ready,
and hands the request to the next one in line.
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from step1_process import ask
from step2_desired import number
from store import read

PORT = 18080
count = 0


def ready_pods(pods):
    """The pods that may get requests: ready, and not on their way out."""
    return sorted((name for name, pod in pods.items() if pod['ready'] and not pod.get('stopping')), key=number)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        global count
        pods = read()['pods']
        ready = ready_pods(pods)
        reply = None
        if ready:
            count += 1
            reply = ask(pods[ready[count % len(ready)]]['port'], self.path)
        body = (reply or 'no pod answered').encode()
        self.send_response(200 if reply else 503)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


if __name__ == '__main__':
    ThreadingHTTPServer.request_queue_size = 128        # many callers may wait in line
    ThreadingHTTPServer.handle_error = lambda *args: None    # a caller that died half way is not an error
    ThreadingHTTPServer(('127.0.0.1', PORT), Handler).serve_forever()
