"""Step 7. A service: one stable address for pods that keep changing.

Pods die and new ones appear on other ports. A client that remembers the
address of one pod is lost. A client that asks the service is not.
"""
import threading
import time

from step1_process import ask
from step6_nodes import TICK, boot, power_off, shutdown, spawn, turn, wait_all_ready
from service import PORT
from store import read


def who(reply):
    """'hello from web-2 (v1)' -> 'web-2'"""
    return reply.split()[2] if reply else None


def tally(replies):
    """['web-1', 'web-2', 'web-1', None] -> {'web-1': 2, 'web-2': 1}"""
    counts = {}
    for name in replies:
        if name:
            counts[name] = counts.get(name, 0) + 1
    return dict(sorted(counts.items()))


class Traffic:
    """A client that sends one request to the service every 20 ms, and writes down every reply."""

    def __init__(self):
        self.log, self.on, self.t0 = [], True, time.time()
        self.thread = threading.Thread(target=self.work)
        self.thread.start()

    def work(self):
        while self.on:
            sent = time.time() - self.t0
            self.log.append((round(sent, 3), ask(PORT, '/', 0.5)))
            time.sleep(0.02)

    def stop(self):
        self.on = False
        self.thread.join()
        return self.log


def run():
    procs = boot({'node-a': 3, 'node-b': 3, 'node-c': 3})
    procs['service'] = spawn('service.py')
    out = {}
    try:
        turn()
        wait_all_ready()
        while ask(PORT) is None:
            time.sleep(0.02)
        out['before'] = tally(who(ask(PORT)) for _ in range(9))
        old_port = read()['pods']['web-2']['port']
        traffic = Traffic()
        time.sleep(0.3)
        out['off_at'] = round(time.time() - traffic.t0, 3)
        power_off(procs, 'node-b')
        time.sleep(0.05)
        out['turns'] = []
        for t in range(6):
            time.sleep(TICK)
            did = turn()
            out['turns'].append((round(time.time() - traffic.t0, 3), did))
        wait_all_ready()
        time.sleep(0.2)
        out['log'] = [(t, who(reply)) for t, reply in traffic.stop()]
        out['failed'] = sum(name is None for _, name in out['log'])
        out['last_fail'] = max((t for t, name in out['log'] if name is None), default=0)
        out['direct'] = sum(ask(old_port, '/', 0.2) is not None for _ in range(6))
        out['after'] = tally(who(ask(PORT)) for _ in range(6))
        return out
    finally:
        shutdown(procs)


if __name__ == '__main__':
    out = run()
    spread = lambda counts: ', '.join(f'{name} {n}' for name, n in counts.items())
    print(f"9 requests to the service on port {PORT}: {spread(out['before'])}")
    print('node-b loses power while a client sends a request every 20 ms')
    for at, did in out['turns']:
        if did:
            print(f"  {at - out['off_at']:.2f} s later: {', '.join(did)}")
    print(f"  {len(out['log'])} requests sent, {out['failed']} failed, the last failure {out['last_fail'] - out['off_at']:.2f} s after the power cut")
    print(f"6 requests to the old address of web-2: {out['direct']} answered")
    print(f"6 requests to the service: {sum(out['after'].values())} answered ({spread(out['after'])})")
