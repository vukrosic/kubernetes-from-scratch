"""The whole thing: a store, three nodes, a service and the controller.

    python3 cluster.py

Leave it running, and in a second terminal talk to it with ctl.py.
"""
import signal
import sys
import time

from step6_nodes import TICK, boot, shutdown, spawn
from step8_rollout import turn

if __name__ == '__main__':
    procs = boot({'node-a': 3, 'node-b': 3, 'node-c': 3}, want=3)
    procs['service'] = spawn('service.py')
    print('the cluster is up. the service listens on http://127.0.0.1:18080   (ctrl-c to stop)')
    signal.signal(signal.SIGTERM, lambda *args: sys.exit(0))       # so that kill also cleans up
    start = time.time()
    try:
        while True:
            for line in turn():
                print(f'{time.time() - start:7.1f} s  {line}')
            time.sleep(TICK)
    except KeyboardInterrupt:
        print()
    finally:
        shutdown(procs)
