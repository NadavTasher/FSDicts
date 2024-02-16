import time
import string
import random
import tempfile
import multiprocessing

from fsdicts import TimeoutLock

from test_storage import storage
from test_database import database

TimeoutLock.TIMEOUT = 10


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


def test_database_kill_during_write(database):
    # Create the large dictionary
    large_dictionary = {"".join(random.sample(list(string.ascii_letters), 10)): "".join(random.sample(list(string.ascii_letters), 10)) for _ in range(1000)}

    def write():
        database.update(large_dictionary)

    process = multiprocessing.Process(target=write)
    process.start()

    # Sleep random amount
    time.sleep(random.random())

    # Kill the process
    process.terminate()

    # Wait for the process to stop
    process.join()

    # Check database integrity
    data = database.copy()

    # Make sure the database was not empty
    assert data


def test_database_multiprocess_kill_during_write(database):
    # Create global things
    manager = multiprocessing.Manager()
    exceptions = manager.list()

    def stress():
        try:
            database.update({"".join(random.sample(list(string.ascii_letters), 10)): "".join(random.sample(list(string.ascii_letters), 10)) for _ in range(100)})
        except BaseException as e:
            # Append failure
            exceptions.append(e)

    # Create many stress processes
    processes = [multiprocessing.Process(target=stress) for _ in range(10)]

    # Execute all processes
    for p in processes:
        p.start()

    # Sleep random amount
    time.sleep(random.random())

    for p in processes:
        # Kill the process
        p.terminate()

    # Wait for all processes
    for p in processes:
        p.join()

    # Check database integrity
    data = database.copy()

    # Make sure the database was not empty
    assert data

    # Raise all of the exceptions
    for e in exceptions:
        raise e
