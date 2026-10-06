#!/bin/sh
# Runs every step in order, then the tests. Takes about a minute.
set -e
cd "$(dirname "$0")"
for step in step1_process step2_desired step3_loop step4_recovery step5_scheduler step6_nodes step7_service step8_rollout exercise_grow; do
  echo
  echo "=== $step.py ==="
  python3 "$step.py"
done
echo
echo "=== tests.py ==="
python3 tests.py
