"""Step 3. The control loop: observe, compare, act. Again and again.

The loop never remembers what it did. Every turn it looks at the real world
and at the wish, and closes the gap. That one habit is the heart of Kubernetes.
"""
import time

from step1_process import start, stop, wait_ready
from step2_desired import plan

TICK = 0.2      # seconds between two turns of the loop


def new_cluster(want, version='v1'):
    return {'want': want, 'version': version, 'pods': {}, 'made': 0}


def observe(cluster):
    """Look at the real world: forget every pod whose process has died."""
    gone = [name for name, pod in cluster['pods'].items() if pod['proc'].poll() is not None]
    for name in gone:
        del cluster['pods'][name]
    return gone


def turn(cluster):
    """One turn of the loop. Returns what it did, in words."""
    did = [f'{name} is gone' for name in observe(cluster)]
    to_start, to_stop = plan(cluster['want'], list(cluster['pods']))
    started = []
    for _ in range(to_start):
        cluster['made'] += 1
        name, port = f"web-{cluster['made']}", 18100 + cluster['made']
        cluster['pods'][name] = {'proc': start(name, port, cluster['version']), 'port': port}
        started.append(name)
    for name in started:
        wait_ready(cluster['pods'][name]['port'])
        did.append(f'start {name}')
    for name in to_stop:
        stop(cluster['pods'].pop(name)['proc'])
        did.append(f'stop {name}')
    return did


def shutdown(cluster):
    for pod in cluster['pods'].values():
        stop(pod['proc'])
    cluster['pods'].clear()


if __name__ == '__main__':
    cluster = new_cluster(want=3)
    wishes = {4: 5, 8: 2}                   # at turn 4 we ask for 5 pods, at turn 8 for 2
    try:
        for t in range(12):
            if t in wishes:
                cluster['want'] = wishes[t]
                print(f'        (we change the wish to {wishes[t]} pods)')
            have = len(cluster['pods'])
            did = turn(cluster)
            print(f"turn {t:2}: want {cluster['want']}, have {have} -> {', '.join(did) or 'nothing to do'}")
            time.sleep(TICK)
        print('running at the end:', ', '.join(cluster['pods']))
    finally:
        shutdown(cluster)
