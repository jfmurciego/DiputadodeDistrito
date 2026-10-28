#!/usr/bin/env python3
"""Hard wall-clock supervisor for the single PV-CUT-02 solver invocation."""
import json
import os
import pathlib
import signal
import subprocess
import sys
import time

root = pathlib.Path(__file__).resolve().parent
script = root / 'pv_rooted_connectivity_cuts.py'
stdout_path = root / 'rooted_stdout.log'
stderr_path = root / 'rooted_stderr.log'
report_path = root / 'rooted_supervisor.json'
python = '/usr/local/Caskroom/miniforge/base/envs/ddd_aragon/bin/python'
hard_timeout = 130.0
start = time.monotonic()
with stdout_path.open('wb') as stdout, stderr_path.open('wb') as stderr:
    proc = subprocess.Popen([python, str(script)], cwd=str(root.parents[2]), stdout=stdout, stderr=stderr, start_new_session=True)
    try:
        returncode = proc.wait(timeout=hard_timeout)
        timed_out = False
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(proc.pid, signal.SIGTERM)
        try:
            returncode = proc.wait(timeout=3.0)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            returncode = proc.wait()
elapsed = time.monotonic() - start
data = {'script': script.name, 'hard_timeout_seconds': hard_timeout, 'elapsed_seconds': elapsed,
        'timed_out': timed_out, 'returncode': returncode,
        'stdout_sha256': __import__('hashlib').sha256(stdout_path.read_bytes()).hexdigest(),
        'stderr_sha256': __import__('hashlib').sha256(stderr_path.read_bytes()).hexdigest(),
        'solver_report_exists': (root / 'rooted_result.json').exists(),
        'assignment_exists': (root / 'rooted_candidate_assignment.json').exists()}
report_path.write_text(json.dumps(data, indent=2) + '\n')
print(json.dumps(data, sort_keys=True))
sys.exit(124 if timed_out else returncode)
