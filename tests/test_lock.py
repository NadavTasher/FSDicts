import os
import time
import tempfile
import threading

from fsdicts import *


def test_lock():
    # Create path to lock on
    path = tempfile.mktemp()

    # FileLock the path
    with FileLock(path) as lock:
        assert os.path.isdir(lock._path)


def test_lock_multithreaded(num_threads=5, thread_sleep=0.2):
    # Create path to lock on
    path = tempfile.mktemp()

    def target(path, sleep):
        # Try locking the path
        with FileLock(path):
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


def test_lock_multithreaded_samelock(num_threads=5, thread_sleep=0.2):
    # Create path to lock on
    path = tempfile.mktemp()
    lock = FileLock(path)

    def target(lock, sleep):
        # Try locking the path
        with lock:
            time.sleep(sleep)

    # Create threads
    threads = [threading.Thread(target=target, args=(lock, thread_sleep)) for _ in range(num_threads)]

    # Mark start time
    start = time.time()

    # Start all threads
    for t in threads:
        t.start()

    for t in threads:
        t.join()

    # Make sure end time is larger then start time by more then num_threads * thread_sleep
    assert (time.time() - start) > float(num_threads * thread_sleep)


def test_lock_nonblocking():
    # Create path to lock on
    path = tempfile.mktemp()

    # Create the lock
    lock = FileLock(path)

    # Try locking the lock
    assert lock.acquire(False)
    assert not lock.acquire(False)

    # Release the lock
    lock.release()

    # Acquire the lock
    assert lock.acquire()

    # Mark start time
    start_time = time.time()

    # Try aquiring the lock
    assert not lock.acquire(timeout=1)

    # Check end time
    assert time.time() - start_time > 1


def test_rlock_references():
    # Create path to lock on
    path = tempfile.mktemp()

    # Create the lock
    lock = FileLock(path)
    mutex = ReferenceLock(lock)

    # FileLock the lock multiple times
    with mutex:
        with mutex:
            with mutex:
                assert mutex._references == 3

    # Check empty references
    assert mutex._references == 0


def test_rlock_multithreaded_samelock(num_threads=5, thread_sleep=0.2):
    # Create path to lock on
    path = tempfile.mktemp()

    # Create the lock
    lock = FileLock(path)
    mutex = ReferenceLock(lock)

    def target(mutex, number):
        # Try locking the path
        with mutex:
            with mutex:
                time.sleep(number)

    # Create threads
    threads = [threading.Thread(target=target, args=(mutex, thread_sleep)) for _ in range(num_threads)]

    # Mark start time
    start = time.time()

    # Start all threads
    for t in threads:
        t.start()

    for t in threads:
        t.join()

    # Make sure end time is larger then start time by more then num_threads * thread_sleep
    assert (time.time() - start) > float(num_threads * thread_sleep)
