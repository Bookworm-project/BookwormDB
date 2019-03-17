import sys
import os
import bounter
from collections import Counter
from tokenizer import tokenizer
from multiprocessing import Process, Queue, Pool
import multiprocessing as mp
import psutil
import queue
import logging
import fileinput
from multiprocessingHelp import mp_stats, running_processes
import time

# Use another third of the memory for storing worker counts; divided
# by number of CPUS.
# Assume 200 bytes per entry in python dict.

cpus, memory = mp_stats()
memory = memory/1024/1024/2

QUEUE_POST_THRESH = int(memory / 3 * 1024 * 1024 / 200 / cpus)
QUEUE_POST_THRESH = min([250000, QUEUE_POST_THRESH])

logging.info("Filling dicts to size {}".format(QUEUE_POST_THRESH))

import random

def counter(qout, i, fin):
    # Counts words exactly in a separate process.
    # It runs in place.
    counter = Counter()
    totals = 0
    errors = 0
    fin = open(fin)
    for ii, row in enumerate(fin):
        if ii % cpus != i:
            # Don't do anything on most lines.
            continue
        totals += 1
        try:
            (filename, text) = row.rstrip().split("\t",1)
        except ValueError:
            errors += 1
            continue
        text = tokenizer(text)
        for q in text.tokenize():
            counter[q] += 1
            # When the counter is long, post it to the master and clear it.
        if len(counter) > QUEUE_POST_THRESH:
            qout.put(counter)
            counter = Counter()
    qout.put(counter)
    if errors/totals > 0.01:
        logging.warning("Skipped {} rows without tabs".format(errors))
    
def main_process(input = "input.txt"):
    qin = Queue(10000)
    qout = Queue(cpus * 2)
    
    workers = []

    for i in range(cpus):
        p = Process(target = counter, args = (qout, i, input))
        p.start()
        workers.append(p)

    wordcounter = bounter.bounter(memory)

    while True
        try:
            wordcounter.update(qout.get_nowait())
        except queue.Empty:
            if running_processes(workers):
                time.sleep(0.01)
            else:
                break
        
    return wordcounter


def write_top_words_from_stdin(n = 100, output = "x"):
    counter = main_process(sys.argv[1])
    counter = sorted(list(counter.iteritems()), key = lambda x: -1 * x[1])
    output = open(output, "w")
    output = sys.stdout
    for i, (k, v) in enumerate(counter):
        output.write("{}\t{}\n".format(v,k))
        if i > n:
            break
    
if __name__=="__main__":
    write_top_words_from_stdin()
