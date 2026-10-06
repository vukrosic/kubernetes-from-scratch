"""Step 2. Desired state: write down what you want, and compare it with what you have.

We do not say "start a pod". We say "there should be 3 pods", and let a
function work out what that means right now.
"""


def number(name):
    """web-12 -> 12, so that web-10 sorts after web-9."""
    return int(name.split('-')[-1])


def plan(want, have):
    """want: how many pods there should be. have: the names of the pods running now.

    Returns (how many to start, which ones to stop).
    """
    if len(have) < want:
        return want - len(have), []
    newest_first = sorted(have, key=number, reverse=True)
    return 0, newest_first[:len(have) - want]


if __name__ == '__main__':
    cases = [(3, []), (3, ['web-1']), (3, ['web-1', 'web-2', 'web-3']),
             (3, ['web-1', 'web-2', 'web-3', 'web-4', 'web-5']), (0, ['web-1', 'web-2'])]
    for want, have in cases:
        to_start, to_stop = plan(want, have)
        todo = (f'start {to_start}' if to_start else '') + ('stop ' + ', '.join(to_stop) if to_stop else '')
        print(f'want {want}, have {len(have)} -> {todo or "nothing to do"}')
