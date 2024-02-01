import pytest
import shutil
import hashlib
import tempfile
import itertools
import multiprocessing

from fsdicts import *


@pytest.fixture(params=itertools.product([LinkStorage, ReferenceStorage], [hashlib.md5, hashlib.sha1, hashlib.sha256, hashlib.sha512], [LocalLock, FileLock]))
def storage(request):
    # Untuple the parameters
    storage_type, hash_type, lock_type = request.param

    # Create the storage
    return storage_type(tempfile.mktemp(), hash=hash_type, lock=lock_type)


def test_put(storage):
    # Make sure storage is empty
    assert not len(storage)

    # Add object to storage
    storage.put(b"Hello")

    # Make sure object was registered
    assert len(storage)


def test_purge(storage):
    # Add object to storage
    storage.put(b"Hello World")

    # Purge the database
    storage.purge()

    # Make sure object was deleted
    assert not len(storage)


def test_usage_purge(storage):
    # Create target reference path
    reference_path = tempfile.mktemp()

    # Add a value to the storage
    identifier = storage.put(b"Hello World!!!")

    # Link the identifier
    storage.link(identifier, reference_path)

    # Purge the storage
    storage.purge()

    # Make sure object was not deleted
    assert len(storage)

    # Unlink the identifier
    storage.unlink(reference_path)

    # Make sure object was deleted
    assert not len(storage)


def test_readlink_purge(storage):
    # Create the value to write
    value = b"Hello World!!!"

    # Create target reference path
    reference_path = tempfile.mktemp()

    # Add a value to the storage
    identifier = storage.put(value)

    # Link the identifier
    storage.link(identifier, reference_path)

    # Purge the storage
    storage.purge()

    # Read the link and compare to value
    assert storage.readlink(reference_path) == value

    # Copy the reference path to a tempfile
    fake_reference_path = tempfile.mktemp()
    shutil.copy(reference_path, fake_reference_path)

    # Unlink the reference
    storage.unlink(reference_path)

    # Try reading the original reference
    with pytest.raises((OSError, IOError)):
        storage.readlink(reference_path)


def test_multiprocess_writes(storage):
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
