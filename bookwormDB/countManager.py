import sys
import os
import bounter
from collections import Counter
from .tokenizer import Tokenizer, tokenBatches, PreTokenized
from multiprocessing import Process, Queue, Pool
from .multiprocessingHelp import mp_stats, running_processes
import multiprocessing as mp
import psutil
import queue
import logging
import fileinput
import time
import csv
from pathlib import Path
import gzip
import hashlib

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

def flush_counter(counter, qout):
    for k in ['', '\x00']:
        try:
            del counter[k]
        except KeyError:
            continue
        qout.put(counter)

def counter(qout, i, fin, mode = "count"):
    """
    # Counts words exactly in a separate process.
    # It runs in place.
    If mode is 'encode', this is called for a side-effect of writing
    files to disk.
    """

    totals = 0
    errors = 0

    if mode == "count":
        counter = Counter()
        encoder = tokenBatches(['words'])

    if mode == "encode":
        encoder = tokenBatches(['unigrams', 'bigrams'])

    datatype = "raw"

    count_signals = [".unigrams", ".bigrams", ".trigrams", ".quadgrams"]
    for signal in count_signals:
        if signal in fin:
            datatype = signal.strip(".")
            if mode == "encode":
                encoder = tokenBatches([datatype])



    for id, text in yield_texts(fin, i):

        if datatype == "raw":
            tokenizer = Tokenizer(text)
        else:
            tokenizer = PreTokenized(text, encoder.levels[0])

        # When encoding
        if mode == "encode":
            encoder.encodeRow(id, tokenizer, write_completed = True)
            continue

        # When building counts
        counter.update(tokenizer.counts("words"))

        # When the counter is long, post it to the master and clear it.
        if len(counter) > QUEUE_POST_THRESH:
            flush_counter(counter=counter, qout = qout)
            counter = Counter()

    # Cleanup.
    if mode == "count":
        logging.debug("Flushing leftover counts from thread {}".format(i))
        flush_counter(counter=counter, qout = qout)
    if mode == "encode":
        encoder.close()

def yield_texts(fname, i):
    p = Path(fname)
    if p.is_dir():
        for id, text in yield_texts_from_directory(p, i):
            yield (id, text)
    else:
        for id, text in yield_lines_from_single_file(p, i):
            yield (id, text)


def yield_texts_from_directory(dir, i):
    for file in dir.glob('**/*.txt*'):
        # Strips _djvu for Internet Archive.
        basename = file.name.rstrip(".gz").rstrip(".txt").rstrip("_djvu")
        # Use sha256
        key = int(hashlib.md5(basename.encode('utf-8')).hexdigest(), 16)
        if key % cpus != i:
            continue
        if file.name.endswith(".txt.gz"):
            fin = gzip.open(file)
        elif file.name.endswith(".txt"):
            fin = open(file)
        else:
            logging.error(f"Can't handle file {file}")
        yield (basename, fin.read().replace("\t", "\f").replace("\n", "\f"))

def yield_lines_from_single_file(fname, i, cpus):
    if (fname.endswith(".gz")):
        fin = gzip.open(fin, 'rt')
    else:
        fin = open(fin)
    totals = 0
    errors = 0
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
        yield (filename, text)
    if totals > 0 and errors/totals > 0.01:
        logging.warning("Skipped {} rows without tabs".format(errors))


def create_counts(input):
    qout = Queue(cpus * 2)
    workers = []
    logging.info("Spawning {} count processes on {}".format(cpus, input))
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
        except TypeError:
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

def encode_words(wordlist, input):
    qout = Queue(cpus * 2)
    workers = []

    for i in range(cpus):
        p = Process(target = counter, args = (qout, i, input, "encode"))
        p.start()
        workers.append(p)

    while running_processes(workers):
        time.sleep(1/30)
