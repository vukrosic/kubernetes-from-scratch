"""Talk to the running cluster.

    python3 ctl.py get              show the nodes and the pods
    python3 ctl.py want 5           ask for 5 pods
    python3 ctl.py version v2       roll out a new version
    python3 ctl.py crash web-1      make one pod crash
    python3 ctl.py kill node-b      cut the power of one node
    python3 ctl.py ask 6            send 6 requests to the service
"""
import os
import signal
import sys
import time

from step1_process import ask
from step2_desired import number
from store import read, write

DEAD_AFTER = 0.6


def table(state, now):
    lines = ['NODE     SLOTS  STATE']
    for name, node in sorted(state['nodes'].items()):
        lines.append(f"{name:8} {node['slots']:<6} {'alive' if now - node['beat'] < DEAD_AFTER else 'dead'}")
    lines.append('')
    lines.append('POD      NODE     VERSION     READY  RESTARTS')
    for name in sorted(state['pods'], key=number):
        pod = state['pods'][name]
        lines.append(f"{name:8} {pod['node']:8} {pod['version']:11} {'yes' if pod['ready'] else 'no':6} {pod['restarts']}")
    return lines


if __name__ == '__main__':
    command, arg = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else '')
    state = read()
    if state is None:
        sys.exit('the cluster is not running. start it with: python3 cluster.py')
    if command == 'get':
        print(f"wish: {state['want']} pods of version {state['version']}\n")
        print('\n'.join(table(state, time.time())))
    elif command == 'want':
        write(['want'], int(arg))
    elif command == 'version':
        write(['version'], arg)
    elif command == 'crash':
        ask(state['pods'][arg]['port'], '/crash', 0.2)
    elif command == 'kill':
        os.killpg(state['nodes'][arg]['pid'], signal.SIGKILL)
    elif command == 'ask':
        for _ in range(int(arg or 1)):
            print(ask(18080) or 'no answer')
