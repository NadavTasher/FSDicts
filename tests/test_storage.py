import os
import pytest
import shutil
import tempfile

from fsdicts import *


@pytest.fixture(params=[LinkStorage, ReferenceStorage])
def storage(request):
    return request.param(tempfile.mktemp())


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
