"""Step 8. A new version, without one failed request.

The store says which version we want. The controller moves one small step
towards it per turn: start one new pod, wait until it answers, then let one
old pod finish and stop it. It never takes an old pod away first.
"""
import time

from step2_desired import number
from step6_nodes import TICK, add_pod, boot, fill, shutdown, spawn, sweep, wait_all_ready
from step7_service import Traffic
from service import PORT
from step1_process import ask
from store import erase, read, write


def rollout(state):
    """One small step from the old version towards the new one."""
    pods = state['pods']
    new = [name for name in pods if pods[name]['version'] == state['version']]
    old = sorted((name for name in pods if name not in new), key=number)
    waiting = [name for name in new if not pods[name]['ready']]
    if waiting:
        return [f'wait: {waiting[0]} does not answer yet']       # never go on before the new pod works
    if len(pods) <= state['want']:
        return [add_pod(state) + f" ({state['version']})"]
    if not pods[old[0]].get('stopping'):
        write(['pods', old[0], 'stopping'], True)                # the service stops sending it requests
        return [f'drain {old[0]}']
    erase(['pods', old[0]])
    return [f'stop {old[0]}']


def turn():
    state = read()
    did = sweep(state)
    if any(pod['version'] != state['version'] for pod in state['pods'].values()):
        return did + rollout(state)
    return did + fill(state)


def versions(log):
    """Count the replies per version. A reply looks like 'hello from web-4 (v2)'."""
    counts = {}
    for _, reply in log:
        key = reply.split('(')[1][:-1] if reply else 'failed'
        counts[key] = counts.get(key, 0) + 1
    return counts


def drive(turns, until=None, first=None):
    """Run the controller for some turns while a client keeps sending requests."""
    traffic = Traffic()
    time.sleep(0.2)
    if first:
        first()
    log = []
    for t in range(turns):
        did = turn()
        log.append((round(time.time() - traffic.t0, 3), did))
        time.sleep(TICK)
        if until and until(read()):
            break
    time.sleep(0.2)
    return log, traffic.stop()


def all_on(version):
    return lambda state: (len(state['pods']) == state['want']
                          and all(p['version'] == version and p['ready'] for p in state['pods'].values()))


def run():
    procs = boot({'node-a': 3, 'node-b': 3, 'node-c': 3})
    procs['service'] = spawn('service.py')
    out = {}
    try:
        turn()
        wait_all_ready()
        while ask(PORT) is None:
            time.sleep(0.02)

        out['rolling'] = drive(30, all_on('v2'), lambda: write(['version'], 'v2'))     # 1. a rolling update

        def stop_all_start_all():                                   # 2. the blunt way
            write(['version'], 'v3')
            for name in read()['pods']:
                erase(['pods', name])
        out['blunt'] = drive(30, all_on('v3'), stop_all_start_all)

        out['broken'] = drive(8, None, lambda: write(['version'], 'v4-broken'))        # 3. a release that crashes on start
        state = read()
        out['broken_pod'] = [(name, pod['restarts']) for name, pod in state['pods'].items() if pod['version'] != 'v3'][0]

        out['back'] = drive(30, lambda state: len(state['pods']) == state['want'],     # 4. take it back
                            lambda: write(['version'], 'v3'))
        out['end'] = {name: pod['version'] for name, pod in read()['pods'].items()}
        return out
    finally:
        shutdown(procs)


def report(title, part):
    turns, log = part
    print(title)
    for i, (_, did) in enumerate(turns):
        print(f"  turn {i}: {', '.join(did) or 'nothing to do'}")
    counts = versions(log)
    failed = counts.pop('failed', 0)
    by = ', '.join(f'{n} by {v}' for v, n in counts.items())
    print(f'  {len(log)} requests sent, {failed} failed; answered: {by}')


if __name__ == '__main__':
    out = run()
    report('rolling update v1 -> v2, one request every 20 ms the whole time:', out['rolling'])
    report('the blunt way v2 -> v3: stop every pod, then start new ones:', out['blunt'])
    report('a broken release, v4-broken, that crashes the moment it starts:', out['broken'])
    name, restarts = out['broken_pod']
    print(f'  {name} was restarted {restarts} times and never answered; the old pods never left')
    report('we write v3 back into the store:', out['back'])
    print('at the end: ' + ', '.join(f'{name} ({v})' for name, v in out['end'].items()))
