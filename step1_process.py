"""Step 1. Run one copy of a program, talk to it, and watch it die.

A pod is one running copy of our program: a real process on this computer.
"""
import http.client
import os
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))


def start(name, port, version='v1'):
    """Start one pod: a real process running app.py."""
    return subprocess.Popen([sys.executable, os.path.join(HERE, 'app.py'), name, str(port), version])


def ask(port, path='/', timeout=0.5):
    """Send one request. Returns the reply, or None if nothing answered in time."""
    try:
        with urllib.request.urlopen(f'http://127.0.0.1:{port}{path}', timeout=timeout) as reply:
            return reply.read().decode()
    except (OSError, http.client.HTTPException):
        return None


def wait_ready(port, seconds=5.0):
    """Wait until the pod answers. A fresh process needs a moment to start."""
    end = time.time() + seconds
    while time.time() < end:
        if ask(port, '/health', 0.2) == 'ok':
            return True
        time.sleep(0.02)
    return False


def stop(proc):
    """Kill the process and wait until it is really gone."""
    proc.kill()
    proc.wait()


if __name__ == '__main__':
    pod = start('web-1', 18101)
    wait_ready(18101)
    print('started web-1: a real process on port 18101')
    for i in range(3):
        print(f'  request {i + 1}: {ask(18101)}')
    stop(pod)
    print('the process is killed, the way a crash would kill it')
    for i in range(3):
        print(f'  request {i + 4}: {ask(18101) or "no answer"}')
    print('nobody restarts it: 3 of 3 requests after the crash got no answer')
