import os
import time
import pytest
import tempfile
import itertools
import threading

from fsdicts import *

lock_types = [FileLock, DirectoryLock]


@pytest.fixture(params=itertools.product(lock_types))
def lock_class(request):
    lock_class,=request.param
    return lock_class

def test_lock(lock_class):
    # Create path to lock on
    path = tempfile.mktemp()

    # Lock the path
    with lock_class(path):
        # Make sure lock can't be acquired
        assert not lock_class(path).acquire(blocking=False), "Lock has failed to be exclusive"
    
    # Try acquiring now
    assert lock_class(path).acquire(blocking=False), "Lock was not released"

def test_double_lock_acquire_timeout(lock_class):
    # Create path to lock on
    path = tempfile.mktemp()

    # Acquire the lock
    with lock_class(path):
        # Mark select time
        start_time = time.time()

        # Try acquiring the lock again
        assert not lock_class(path).acquire(blocking=True, timeout=3), "Lock was acquired but it shouldn't have been possible"

        # Make sure at least 3 seconds have passed
        assert time.time() - start_time >= 3, "Not enough time has passed"

def test_lock_multithreaded(lock_class, num_threads=10, thread_sleep=0.2):
    # Create path to lock on
    path = tempfile.mktemp()

    def target(path, sleep):
        # Try locking the path
        with lock_class(path):
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


def test_lock_multithreaded_samelock(lock_class, num_threads=5, thread_sleep=0.2):
    # Create path to lock on
    path = tempfile.mktemp()
    lock = lock_class(path)

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


def test_lock_nonblocking(lock_class):
    # Create path to lock on
    path = tempfile.mktemp()

    # Create the lock
    lock = lock_class(path)

    # Try locking the lock
    assert lock.acquire(False)
    assert not lock_class(path).acquire(False)

    # Release the lock
    lock.release()

    # Acquire the lock
    assert lock.acquire()

    # Mark start time
    start_time = time.time()

    # Try aquiring the lock
    assert not lock_class(path).acquire(timeout=1)

    # Check end time
    assert time.time() - start_time > 1


def test_timeout_lock(lock_class):
    # Create path to lock on
    path = tempfile.mktemp()

    # Create a custom class with the TimeoutLock mixin
    class CustomTimeoutLock(lock_class, TimeoutLock):
        pass

    # Create the lock
    lock = CustomTimeoutLock(path, 4)

    # Try locking the lock
    time_a = time.time()
    lock.acquire()
    time_b = time.time()
    lock.acquire()
    time_c = time.time()

    # Make sure the times allign
    assert time_b - time_a < 1
    assert time_c - time_b > 3
