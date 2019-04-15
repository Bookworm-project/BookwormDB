import os
import psutil
import logging

def mp_stats():
    try:
        cpus = len(os.sched_getaffinity(0))
    except AttributeError:
        # Should be better OS X support than this.
        cpus = 6

    # Allocate half of available memory for the bounter
    memory = int(psutil.virtual_memory()[4])

    if memory < 1024:
        logging.warning("Not much memory to work with--vocab may be exact")

    return (cpus, memory)

def running_processes(workerlist):
    running = False
    for worker in workerlist:
        if worker.is_alive():
            running = True
        else:
            code = worker.exitcode
            if code > 0:
                raise("Process died with code {}".format(code))
    return running
