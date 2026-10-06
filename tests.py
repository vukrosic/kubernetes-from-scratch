"""Tests for every step. Run: python3 tests.py"""
import time

import step3_loop
import step4_recovery
import step6_nodes
import step7_service
import step8_rollout
import exercise_grow
from step1_process import ask, start, stop, wait_ready
from step2_desired import plan
from step5_scheduler import first_fit, free, place, schedule
from service import ready_pods

passed = 0


def check(name, ok):
    global passed
    assert ok, name
    passed += 1
    print(f'ok  {name}')


# step 1
pod = start('web-1', 18101)
check('a started pod answers', wait_ready(18101) and ask(18101) == 'hello from web-1 (v1)')
stop(pod)
check('a killed pod does not answer', ask(18101) is None)

# step 2
check('plan: nothing running -> start all', plan(3, []) == (3, []))
check('plan: equal -> nothing', plan(3, ['web-1', 'web-2', 'web-3']) == (0, []))
check('plan: too many -> stop the newest', plan(1, ['web-2', 'web-9', 'web-10']) == (0, ['web-10', 'web-9']))

# step 3
cluster = step3_loop.new_cluster(want=3)
try:
    check('loop: first turn starts 3', step3_loop.turn(cluster) == ['start web-1', 'start web-2', 'start web-3'])
    check('loop: second turn does nothing', step3_loop.turn(cluster) == [])
    cluster['want'] = 1
    check('loop: a smaller wish stops pods', step3_loop.turn(cluster) == ['stop web-3', 'stop web-2'])
    stop(cluster['pods']['web-1']['proc'])
    check('loop: a crashed pod is replaced', step3_loop.turn(cluster) == ['web-1 is gone', 'start web-4'])
    check('loop: the new pod answers', ask(cluster['pods']['web-4']['port']) == 'hello from web-4 (v1)')
finally:
    step3_loop.shutdown(cluster)

# step 4
log, (ok, sent), pods = step4_recovery.run(with_check=False)
check('hung pod without a health check stays', pods == ['web-1', 'web-2', 'web-3'] and (ok, sent) == (8, 12))
log, (ok, sent), pods = step4_recovery.run(with_check=True)
check('hung pod with a health check is replaced', pods == ['web-1', 'web-3', 'web-4'] and (ok, sent) == (12, 12))
check('it is killed on the third silent turn', 'kill web-2' in log[2][1] and 'kill web-2' not in log[1][1])

# step 5
nodes = {'node-a': 3, 'node-b': 3, 'node-c': 3}
check('scheduler spreads', [p['node'] for p in place(nodes, 3, schedule).values()] == ['node-a', 'node-b', 'node-c'])
check('first fit packs', [p['node'] for p in place(nodes, 3, first_fit).values()] == ['node-a'] * 3)
full = place(nodes, 9, schedule)
check('9 pods fill 9 slots', free(nodes, full) == {'node-a': 0, 'node-b': 0, 'node-c': 0})
check('the 10th pod has no node', schedule(nodes, full) is None)
check('a full node is filtered out', schedule({'node-a': 1, 'node-b': 3}, {'x': {'node': 'node-a'}}) == 'node-b')

# step 6
out = step6_nodes.run()
check('nodes: one pod per node', out['turns'][0][1] == ['start web-1 on node-a', 'start web-2 on node-b', 'start web-3 on node-c'])
check('nodes: the agent restarts a crashed pod, the controller does nothing',
      out['crash']['restarts'] == 1 and out['crash']['controller'] == [])
moved = [did for _, did, _ in out['turns'][1:] if did]
check('nodes: a dead node loses its pod, a new one starts elsewhere',
      moved == [['node-b is silent: web-2 is lost', 'start web-4 on node-a']])
check('nodes: dead only after the limit', 500 < out['dead_ms'] < 1000)

# step 7
check('service: only ready pods that are not stopping', ready_pods({
    'web-2': {'ready': True}, 'web-10': {'ready': True}, 'web-3': {'ready': False},
    'web-4': {'ready': True, 'stopping': True}}) == ['web-2', 'web-10'])
out = step7_service.run()
check('service: 9 requests, 3 per pod', out['before'] == {'web-1': 3, 'web-2': 3, 'web-3': 3})
check('service: the old address is dead', out['direct'] == 0)
check('service: all 6 answered by the 3 live pods', out['after'] == {'web-1': 2, 'web-3': 2, 'web-4': 2})
check('service: some requests fail before the node is declared dead', 0 < out['failed'] < len(out['log']) / 2)

# step 8
out = step8_rollout.run()
counts = step8_rollout.versions(out['rolling'][1])
check('rolling update: no failed request', 'failed' not in counts and counts['v1'] > 0 and counts['v2'] > 0)
check('rolling update: start, drain, stop, three times',
      [d[0].split()[0] for _, d in out['rolling'][0] if not d[0].startswith('wait')] == ['start', 'drain', 'stop'] * 3)
check('stop all, start all: requests fail', step8_rollout.versions(out['blunt'][1]).get('failed', 0) > 0)
counts = step8_rollout.versions(out['broken'][1])
check('broken release: every request still answered by v3', list(counts) == ['v3'])
check('broken release: the new pod keeps crashing', out['broken_pod'][1] > 3)
check('rollback: 3 pods of v3 remain', sorted(out['end'].values()) == ['v3', 'v3', 'v3'])

# exercise
out = exercise_grow.run()
check('exercise: 6 start, 3 wait', (out['started'], out['waiting']) == (6, 3))
check('exercise: a new node takes the 3 waiting pods', out['after'] == {'node-a': 3, 'node-b': 3, 'node-c': 3, 'node-d': 3} and out['ready'] == 12)

print(f'\n{passed} tests passed')
