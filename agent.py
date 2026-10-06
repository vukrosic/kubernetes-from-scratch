"""The node agent: one per node. It runs the pods the store gives to its node.

    python3 agent.py node-a 3       (a node called node-a with 3 slots)

It is the loop from step 3 again, for one node: read what should run here,
look at what does run here, close the gap. Kubernetes calls it the kubelet.
"""
import os
import sys
import time

from step1_process import ask, start, stop
from store import read, write

BEAT = 0.05     # seconds between two turns of the agent

name, slots = sys.argv[1], int(sys.argv[2])
running = {}    # pod name -> its process

while True:
    write(['nodes', name], {'slots': slots, 'beat': time.time(), 'pid': os.getpid()})     # "I am alive"
    state = read()
    if state is None:
        time.sleep(BEAT)
        continue
    mine = {pod: info for pod, info in state['pods'].items() if info['node'] == name}
    for pod in [p for p in running if p not in mine]:
        stop(running.pop(pod))
    for pod, info in mine.items():
        if pod not in running:
            running[pod] = start(pod, info['port'], info['version'])
        elif running[pod].poll() is not None:                           # it crashed: start it again
            running[pod] = start(pod, info['port'], info['version'])
            write(['pods', pod, 'restarts'], info['restarts'] + 1)
        ready = ask(info['port'], '/health', 0.2) == 'ok'
        if ready != info['ready']:
            write(['pods', pod, 'ready'], ready)
    time.sleep(BEAT)
