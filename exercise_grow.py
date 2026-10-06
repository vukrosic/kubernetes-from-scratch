"""Exercise. Ask for more pods than the cluster has room for, then add a node.

Three nodes with 3 slots each hold 9 pods. We ask for 12.
"""
import time

from step6_nodes import TICK, boot, shutdown, spawn, wait_all_ready
from step8_rollout import turn
from store import read, write


def per_node(state):
    counts = {name: 0 for name in sorted(state['nodes'])}
    for pod in state['pods'].values():
        counts[pod['node']] += 1
    return counts


def run():
    procs = boot({'node-a': 3, 'node-b': 3, 'node-c': 3}, want=3)
    out = {}
    try:
        turn()
        write(['want'], 12)
        did = turn()
        out['started'] = sum(line.startswith('start') for line in did)
        out['waiting'] = sum(line.startswith('a pod waits') for line in did)
        out['before'] = per_node(read())
        procs['node-d'] = spawn('agent.py', 'node-d', 3)           # plug in one more computer
        while 'node-d' not in read()['nodes']:
            time.sleep(0.02)
        out['after_turn'] = turn()
        wait_all_ready()
        state = read()
        out['after'] = per_node(state)
        out['ready'] = sum(pod['ready'] for pod in state['pods'].values())
        return out
    finally:
        shutdown(procs)


if __name__ == '__main__':
    out = run()
    spread = lambda counts: ', '.join(f'{name} {n}' for name, n in counts.items())
    print(f"the wish goes from 3 to 12: {out['started']} pods start, {out['waiting']} wait for room")
    print(f"  {spread(out['before'])}")
    print('we start one more agent, node-d, with 3 slots')
    print(f"  next turn: {', '.join(out['after_turn'])}")
    print(f"  {spread(out['after'])}; {out['ready']} of 12 pods answer")
