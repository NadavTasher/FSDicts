import time
import pytest
import random
import tempfile
import threading

from fsdicts import *


def test_lock():
    # Create path to lock on
    path = tempfile.mktemp()

    # Lock the path
    with Lock(path) as lock:
        assert os.path.isdir(lock._path)


def test_lock_multithreaded(num_threads=5, thread_sleep=0.2):
    # Create path to lock on
    path = tempfile.mktemp()

    def target(path, sleep):
        # Try locking the path
        with Lock(path):
            time.sleep(sleep)

    # Create threads
    threads = [threading.Thread(target=target, args=(path, thread_sleep)) for _ in range(num_threads)]

    # Mark start time
    start = time.time()

    # Start all threads
    for t in threads:
        t.start()

    for t in threads:
        t.join()

    # Make sure end time is larger then start time by more then num_threads * thread_sleep
    assert (time.time() - start) > float(num_threads * thread_sleep)
