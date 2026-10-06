# Build Kubernetes From Scratch

A miniature container orchestrator in plain Python, built in 8 steps. It keeps a set of
real programs running on three pretend computers, restarts what crashes, moves work off a
dead computer, gives everything one stable address, and swaps in a new version without a
single failed request.

It is a teaching model, not Kubernetes. No containers, no network of machines: every "pod"
is a real process on your own computer, and every "node" is a real process that owns its
pods. The ideas are the real ones: desired state, control loops, a scheduler, node
heartbeats, services, rolling updates.

Needs Python 3.9 or newer. No packages to install.

## Run it

```bash
./run_all.sh
```

That runs every step and the 35 tests (about a minute). `demo-output.txt` holds the output
of one such run. Timings in milliseconds differ a little from run to run.

To play with the finished cluster, use two terminals:

```bash
python3 cluster.py
```

```bash
python3 ctl.py get
python3 ctl.py ask 6
python3 ctl.py want 5
python3 ctl.py version v2
python3 ctl.py crash web-1
python3 ctl.py kill node-b
```

## The steps

| File | What it adds | What you see |
| --- | --- | --- |
| `app.py` | the workload: a tiny web server | `hello from web-1 (v1)` |
| `step1_process.py` | start one pod, talk to it, kill it | after the crash 3 of 3 requests get no answer |
| `step2_desired.py` | `plan(want, have)`: compare the wish with reality | want 3, have 5 → stop web-5, web-4 |
| `step3_loop.py` | the control loop: observe, compare, act | change the wish to 5 and two pods appear |
| `step4_recovery.py` | a crashed pod is replaced; a hung pod is found by a health check | without the check 8 of 12 requests answered, with it 12 of 12 |
| `step5_scheduler.py` | nodes with slots; filter, then score | first-fit loses 3 of 3 pods when node-a dies, spreading loses 1 |
| `store.py`, `agent.py`, `step6_nodes.py` | a shared store, one agent per node, heartbeats | a node loses power and its pod is running elsewhere about a second later |
| `service.py`, `step7_service.py` | one address in front of changing pods | the old pod address answers 0 of 6, the service 6 of 6 |
| `step8_rollout.py` | rolling update, and what a broken release does | v1 → v2 with 0 failed requests; a release that crashes never replaces an old pod |
| `cluster.py`, `ctl.py` | the whole thing, and a small command tool | |
| `exercise_grow.py` | ask for 12 pods on 9 slots, then add a node | 3 pods wait, then land on node-d |

## Which part is which in real Kubernetes

| Here | Kubernetes |
| --- | --- |
| a process running `app.py` | a container in a pod |
| `store.py` | the API server, with etcd behind it |
| `plan` + `fill` + `rollout` in the controller | the ReplicaSet and Deployment controllers |
| `schedule` | kube-scheduler (filtering, then scoring) |
| `agent.py` | the kubelet |
| `service.py` | a Service, with kube-proxy doing the forwarding |
| `ctl.py` | kubectl |

## What is left out

Containers and images, real networking between machines, a store that survives its own
crash (etcd keeps several copies), security, CPU and memory requests (a pod here takes one
slot), restart back-off, watch streams (everything here polls), and a few hundred other
things. Ports 18000 to 18200 on localhost must be free.

## Exercises

1. Run `exercise_grow.py`, then change it so node-d has only 2 slots. What happens to the last pod?
2. In `agent.py`, add the health check from step 4: a pod that is silent three turns in a row is killed.
3. In `step5_scheduler.py`, give pods a size (1 or 2 slots) and make the filter respect it.

MIT licence.
