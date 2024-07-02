
import datetime

procs = []

def _b(task: str = None):
    if procs:
        prev = procs.pop()
        print(f"__B__       {prev[0]}   =>  {(datetime.datetime.now() - prev[1]).total_seconds() * 1000} ms")
    if task:
        procs.append((task, datetime.datetime.now()))