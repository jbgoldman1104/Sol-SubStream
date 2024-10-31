import env
import datetime

procs = []

def _b(task: str = None):
    if not env.DEBUG : return
    if procs:
        prev = procs.pop()
        print(f"__B__       {prev[0]}   =>  {round((datetime.datetime.now() - prev[1]).total_seconds() * 1000, 2)} ms")
    if task:
        procs.append((task, datetime.datetime.now()))