# SPDX-FileCopyrightText: 2024 Tobias Kaiser <mail@tb-kaiser.de>
# SPDX-License-Identifier: Apache-2.0

from .target import TargetId
import time
import sys

def monitor(sess: "BuildSession", refresh_interval: float = 10.0):
    """
    Continuously monitors build directory of provided sess. The build directory
    state is refreshed every refresh_interval seconds. When a target changes
    its state to incomplete (started) or finished, a message is printed to
    stdout.
    """

    status_last = None
    status = None
    while True:
        status_last = status
        status = {}
        for block_id in sess.flow:
            block = sess.flow[block_id]
            for task_id, task in block.tasks.items():
                if task.always_rebuild or task.hidden:
                    continue
                tid = TargetId(block_id, task_id)
                if tid in sess.results:
                    status[tid] = f"finished on {sess.results[tid].time_finished:%y-%m-%d %H:%M}"
                elif tid in sess.incomplete:
                    status[tid] = "started"
                else:
                    status[tid] = "missing"

        if status_last != None:
            for tid in status:
                if status[tid] == "missing":
                    continue
                if status[tid] != status_last[tid]:
                    print(f"{tid}: {status[tid]}")
                    sys.stdout.flush()
        
        time.sleep(refresh_interval)
        sess.reload_results()
