import os
import time
import shutil
import string
import random
import tempfile
import multiprocessing

from test_storage import storage
from test_database import database


def test_storage_multiprocess_writes(storage):
    # Create global things
    manager = multiprocessing.Manager()
    exceptions = manager.list()

    def stress():
        for _ in range(100):
            try:
                # Create random data
                content = b"A" * 1024 * 1024

                # Write to database
                link = tempfile.mktemp()
                identifier = storage.put(content, link)
                storage.unlink(link)
            except BaseException as e:
                # Append failure
                exceptions.append(e)

    # Create many stress processes
    processes = [multiprocessing.Process(target=stress) for _ in range(10)]

    # Execute all processes
    for p in processes:
        p.start()

    # Wait for all processes
    for p in processes:
        p.join()

    # Raise all of the exceptions
    for e in exceptions:
        raise e


def test_database_multiprocess_rewrites(database):
    # Create global things
    manager = multiprocessing.Manager()
    exceptions = manager.list()

    large_dictionary = {"".join(random.sample(list(string.ascii_letters), 10)): "".join(random.sample(list(string.ascii_letters), 10)) for _ in range(100)}

    def stress():
        for _ in range(10):
            try:
                database.update(large_dictionary)
            except BaseException as e:
                # Append failure
                exceptions.append(e)

    # Create many stress processes
    processes = [multiprocessing.Process(target=stress) for _ in range(10)]

    # Execute all processes
    for p in processes:
        p.start()

    # Wait for all processes
    for p in processes:
        p.join()

    # Raise all of the exceptions
    for e in exceptions:
        raise e


def test_database_multiprocess_kill_writes(database):
    # Create the large dictionary
    large_dictionary = {"".join(random.sample(list(string.ascii_letters), 10)): "".join(random.sample(list(string.ascii_letters), 10)) for _ in range(1000)}

    def write():
        database.update(large_dictionary)

    process = multiprocessing.Process(target=write)
    process.start()

    # Sleep random amount
    time.sleep(random.random() / 100.0)

    # Kill the process
    process.kill()

    # Join the process
    process.join()

    # Check database integrity
    data = database.copy()


def notest_database_multiprocess_partial_writes(database):
    # Create global things
    manager = multiprocessing.Manager()
    exceptions = manager.list()

    tmp_lock_directory = os.path.join(tempfile.gettempdir(), __name__)

    large_dictionary = {"".join(random.sample(list(string.ascii_letters), 10)): "".join(random.sample(list(string.ascii_letters), 10)) for _ in range(100)}

    def stress():
        for _ in range(10):
            try:
                database.update(large_dictionary)
            except BaseException as e:
                # Append failure
                exceptions.append(e)

    # Create many stress processes
    processes = [multiprocessing.Process(target=stress) for _ in range(10)]

    # Execute all processes
    for p in processes:
        p.start()

    for p in processes:
        # Sleep random amount
        time.sleep(random.random() / 1000.0)

        # Kill the process
        p.kill()

        # Clear all locks
        shutil.rmtree(tmp_lock_directory, ignore_errors=True)

    # Clear all locks
    shutil.rmtree(tmp_lock_directory, ignore_errors=True)

    # Wait for all processes
    for p in processes:
        p.join()

    # Clear all locks
    shutil.rmtree(tmp_lock_directory, ignore_errors=True)

    # Check database integrity
    data = database.copy()

    # Raise all of the exceptions
    for e in exceptions:
        raise e
