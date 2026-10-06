"""Step 6. Real nodes: every node is its own program, and a node can die.

The controller no longer starts anything. It only writes into the store:
"web-4 belongs on node-a". The agent on node-a reads that and does the work.
"""
import os
import signal
import subprocess
import sys
import time

from step1_process import ask
from step2_desired import plan
from step5_scheduler import schedule
from store import erase, read, write

HERE = os.path.dirname(os.path.abspath(__file__))
TICK = 0.2          # seconds between two turns of the controller
DEAD_AFTER = 0.6    # a node that was silent this long counts as dead


def spawn(script, *args):
    return subprocess.Popen([sys.executable, os.path.join(HERE, script), *map(str, args)], start_new_session=True)


def boot(nodes, want=3):
    """Start the store, then one agent per node. Returns the processes."""
    procs = {'store': spawn('store.py')}
    while read() is None:
        time.sleep(0.02)
    write(['want'], want)
    for name, slots in nodes.items():
        procs[name] = spawn('agent.py', name, slots)
    while len(read()['nodes']) < len(nodes):
        time.sleep(0.02)
    return procs


def power_off(procs, name):
    """Cut the power: the agent and every pod on that node die in the same instant."""
    os.killpg(procs[name].pid, signal.SIGKILL)
    procs.pop(name).wait()


def shutdown(procs):
    for name in sorted(procs):      # nodes first, the store last
        power_off(procs, name)


def alive(state):
    """The nodes we heard from lately, with their slots."""
    now = time.time()
    return {name: node['slots'] for name, node in state['nodes'].items() if now - node['beat'] < DEAD_AFTER}


def sweep(state):
    """Pods on a silent node are lost. Take them out of the store."""
    live, did = alive(state), []
    for name, pod in list(state['pods'].items()):
        if pod['node'] not in live:
            erase(['pods', name])
            del state['pods'][name]
            did.append(f"{pod['node']} is silent: {name} is lost")
    return did


def add_pod(state):
    """Pick a node for one new pod and write the pod into the store."""
    node = schedule(alive(state), state['pods'])
    if node is None:
        return 'a pod waits: no node has room'
    state['made'] += 1
    name = f"web-{state['made']}"
    state['pods'][name] = {'node': node, 'port': 18100 + state['made'], 'version': state['version'],
                           'ready': False, 'restarts': 0}
    write(['made'], state['made'])
    write(['pods', name], state['pods'][name])
    return f"start {name} on {node}"


def fill(state):
    """Steps 2 and 3 again: compare the wish with the pods in the store."""
    to_start, to_stop = plan(state['want'], list(state['pods']))
    did = [add_pod(state) for _ in range(to_start)]
    for name in to_stop:
        erase(['pods', name])
        did.append(f'stop {name}')
    return did


def turn():
    state = read()
    return sweep(state) + fill(state)


def wait_all_ready(seconds=5.0):
    end = time.time() + seconds
    while time.time() < end:
        state = read()
        if len(state['pods']) == state['want'] and all(p['ready'] for p in state['pods'].values()):
            return True
        time.sleep(0.02)
    return False


def where(state):
    return ', '.join(f"{name} on {pod['node']}" for name, pod in state['pods'].items())


def run():
    """The demo, as data: a pod crash, then a node that loses power."""
    procs = boot({'node-a': 3, 'node-b': 3, 'node-c': 3})
    out = {'turns': [], 'crash': {}}
    try:
        out['turns'].append((0, turn()))
        wait_all_ready()
        port = read()['pods']['web-1']['port']
        ask(port, '/crash', 0.2)
        t0 = time.time()
        while ask(port, '/', 0.1) is None:
            time.sleep(0.005)
        out['crash'] = {'back_ms': round((time.time() - t0) * 1000), 'restarts': read()['pods']['web-1']['restarts'],
                        'controller': turn()}
        power_off(procs, 'node-b')
        off = time.time()
        time.sleep(0.05)
        for t in range(1, 8):
            time.sleep(TICK)
            state = read()
            silent = round(time.time() - state['nodes']['node-b']['beat'], 2)
            did = turn()
            out['turns'].append((t, did, silent))
            if did and 'dead_ms' not in out:
                out['dead_ms'] = round((time.time() - off) * 1000)
                wait_all_ready()
                out['back_ms'] = round((time.time() - off) * 1000)
        out['where'] = where(read())
        return out
    finally:
        shutdown(procs)


if __name__ == '__main__':
    out = run()
    print('3 nodes, each one a real program with 3 slots. the wish: 3 pods')
    print(f"turn 0: {', '.join(out['turns'][0][1])}")
    c = out['crash']
    print(f"        (web-1 crashes) its node agent starts it again: it answers after {c['back_ms']} ms, restarts: {c['restarts']}")
    print(f"        the controller saw: {', '.join(c['controller']) or 'nothing to do'}")
    print('        (node-b loses power: its agent and its pods die together)')
    for t, did, silent in out['turns'][1:]:
        print(f"turn {t}: node-b silent for {silent:.2f} s -> {', '.join(did) or 'nothing to do'}")
    print(f"at the end: {out['where']}")
    print(f"node-b was declared dead after {out['dead_ms']} ms; 3 pods answered again after {out['back_ms']} ms")
