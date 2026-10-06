"""Step 5. Many computers: which one gets the next pod?

A node is one computer in the cluster. Here a node is just a name and a number
of slots, and every pod takes one slot. The scheduler does two things:
filter (which nodes can take it at all?) and score (which of those is best?).
"""


def free(nodes, pods):
    """How many empty slots each node has left."""
    left = dict(nodes)
    for pod in pods.values():
        if pod['node'] in left:
            left[pod['node']] -= 1
    return left


def schedule(nodes, pods):
    """Pick a node for one new pod. Returns None if no node has room."""
    left = free(nodes, pods)
    fits = [name for name in sorted(left) if left[name] > 0]        # filter
    if not fits:
        return None
    return max(fits, key=lambda name: left[name])                   # score: the emptiest node wins


def first_fit(nodes, pods):
    """The lazy way: take the first node that has room."""
    left = free(nodes, pods)
    fits = [name for name in sorted(left) if left[name] > 0]
    return fits[0] if fits else None


def place(nodes, count, pick):
    """Place count pods one after another. Returns {pod name: {'node': ...}}."""
    pods = {}
    for i in range(1, count + 1):
        node = pick(nodes, pods)
        if node is None:
            break
        pods[f'web-{i}'] = {'node': node}
    return pods


def show(nodes, pods):
    return '   '.join(f"{name} [{' '.join(p.split('-')[1] for p in pods if pods[p]['node'] == name):5}]"
                      for name in sorted(nodes))


if __name__ == '__main__':
    nodes = {'node-a': 3, 'node-b': 3, 'node-c': 3}
    for label, pick in (('first node with room', first_fit), ('emptiest node wins  ', schedule)):
        pods = place(nodes, 3, pick)
        alive = [p for p in pods if pods[p]['node'] != 'node-a']
        print(f'{label}: {show(nodes, pods)}   node-a dies -> {len(alive)} of 3 pods still run')
    print('now keep adding pods, emptiest node first:')
    pods = {}
    for i in range(1, 11):
        node = schedule(nodes, pods)
        if node is None:
            print(f'  web-{i} -> no node has room: it waits')
            break
        pods[f'web-{i}'] = {'node': node}
        print(f'  web-{i} -> {node}   {show(nodes, pods)}')
