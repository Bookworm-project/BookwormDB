import sys
import os
import bounter
from collections import Counter
from .tokenizer import tokenizer, tokenBatches
from multiprocessing import Process, Queue, Pool
from .multiprocessingHelp import mp_stats, running_processes
import multiprocessing as mp
import psutil
import queue
import logging
import fileinput
import time

cpus, memory = mp_stats()


# Allocate half of available memory for the bounter, in megabytes.
memory = int(memory/1024/1024/2)

# Use another third of the memory for storing worker counts; divided
# by number of CPUS.
# Assume 200 bytes per entry in python dict.

QUEUE_POST_THRESH = int(memory / 3 * 1024 * 1024 / 200 / cpus)
logging.debug("Ideal queue size is {}".format(QUEUE_POST_THRESH))
QUEUE_POST_THRESH = max([100000, QUEUE_POST_THRESH])

logging.info("Filling dicts to size {}".format(QUEUE_POST_THRESH))

import random
import gzip

def counter(qout, i, fin, mode = "count"):
    # Counts words exactly in a separate process.
    # It runs in place.
    totals = 0
    errors = 0
    
    if mode == "count":
        counter = Counter()

    if mode == "encode":
        encoder = tokenBatches(['unigrams', 'bigrams'])
        
    if (fin.endswith(".gz")):
        fin = gzip.open(fin, 'rt')
    else:
        fin = open(fin)
        
    for ii, row in enumerate(fin):
        if ii % cpus != i:
            # Don't do anything on most lines.
            continue
        totals += 1

        # When encoding
        if mode == "encode":
            encoder.encodeRow(row, source = "raw_text", write_completed = True)
            continue
        
        # When building counts
        try:
            (filename, text) = row.rstrip().split("\t",1)
        except ValueError:
            errors += 1
            continue
        text = tokenizer(text)
        for q in text.tokenize():
            if q is not None:
                counter[q] += 1
            # When the counter is long, post it to the master and clear it.
        if len(counter) > QUEUE_POST_THRESH:
            for k in ['', '\x00']:
                try:
                    del counter[k]
                except KeyError:
                    continue
                
            qout.put(counter)
            counter = Counter()

    # Cleanup.
    if mode == "count":
        qout.put(counter)
        if totals > 0 and errors/totals > 0.01:
            logging.warning("Skipped {} rows without tabs".format(errors))
    if mode == "encode":
        encoder.close()
        
        
def create_counts(input):
    qout = Queue(cpus * 2)
    workers = []

    for i in range(cpus):
        p = Process(target = counter, args = (qout, i, input, "count"))
        p.start()
        workers.append(p)

    wordcounter = bounter.bounter(memory)
    
    while True:
        try:
            input_dict = qout.get_nowait()
            logging.debug("inputting queue of length {} from worker".format(len(input_dict)))

            wordcounter.update(input_dict)
        except queue.Empty:
            if running_processes(workers):
                time.sleep(1/100)
            else:
                break
        except ValueError:
            for k, v in input_dict.items():
                print("'{}'\t'{}'".format(k, v))                
                wordcounter.update({k: v})
            raise
    return wordcounter

def create_wordlist(n, input, output):
    counter = create_counts(input)
    counter = sorted(list(counter.iteritems()), key = lambda x: -1 * x[1])
    output = open(output, "w")
    for i, (k, v) in enumerate(counter):
        output.write("{}\t{}\t{}\n".format(i, k, v))
        if i >= n:
            break
        
def encode_words(wordlist, input = "input.txt"):
    qout = Queue(cpus * 2)
    workers = []

    for i in range(cpus):
        p = Process(target = counter, args = (qout, i, input, "encode"))
        p.start()
        workers.append(p)

    while running_processes(workers):
        time.sleep(1/30)
