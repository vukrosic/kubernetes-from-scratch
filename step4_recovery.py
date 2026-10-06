"""Step 4. Recovery: a crashed pod, and a pod that hangs.

A crash is easy: the process is gone, and the loop from step 3 replaces it.
A hung pod is harder: the process is alive, but it never answers. So every
turn we also ask each pod "are you ok?".
"""
import time

from step1_process import ask, stop
from step3_loop import TICK, new_cluster, shutdown, turn

LIMIT = 3       # this many silent turns in a row, and the pod is killed


def check(cluster):
    """Ask every pod for /health. Kill a pod that stays silent LIMIT turns in a row."""
    did = []
    for name, pod in cluster['pods'].items():
        if ask(pod['port'], '/health', 0.2) == 'ok':
            pod['strikes'] = 0
            continue
        pod['strikes'] = pod.get('strikes', 0) + 1
        did.append(f"{name} is silent ({pod['strikes']} of {LIMIT})")
        if pod['strikes'] == LIMIT:
            stop(pod['proc'])
            did.append(f'kill {name}')
    return did


def answers(cluster, rounds=4):
    """Send requests to every pod in turn. Returns (answered, sent)."""
    replies = [ask(pod['port'], '/', 0.2) for _ in range(rounds) for pod in cluster['pods'].values()]
    return sum(r is not None for r in replies), len(replies)


def run(with_check, turns=8):
    cluster = new_cluster(want=3)
    log = []
    try:
        turn(cluster)
        ask(cluster['pods']['web-2']['port'], '/freeze', 0.2)       # web-2 hangs from now on
        for t in range(turns):
            did = (check(cluster) if with_check else []) + turn(cluster)
            log.append((t, did))
            time.sleep(TICK)
        return log, answers(cluster), list(cluster['pods'])
    finally:
        shutdown(cluster)


if __name__ == '__main__':
    cluster = new_cluster(want=3)
    try:
        print('a crash:')
        print(f"  turn 0: {', '.join(turn(cluster))}")
        stop(cluster['pods']['web-2']['proc'])
        print('          (web-2 crashes)')
        print(f"  turn 1: {', '.join(turn(cluster))}")
        print(f"  turn 2: {', '.join(turn(cluster)) or 'nothing to do'}")
    finally:
        shutdown(cluster)
    for with_check in (False, True):
        log, (ok, sent), pods = run(with_check)
        print('a hung pod, ' + ('and every turn we ask "are you ok?":' if with_check else 'and we only look at "is the process alive":'))
        for t, did in log:
            print(f"  turn {t}: {', '.join(did) or 'nothing to do'}")
        print(f"  after 8 turns: {', '.join(pods)}; {ok} of {sent} requests answered")
