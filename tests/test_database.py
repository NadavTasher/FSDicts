import pytest
import tempfile
import itertools

from fsdicts import *


@pytest.fixture(params=itertools.product([PYTHON, JSON], [Dictionary, BunchDictionary], [LinkStorage, ReferenceStorage]))
def database(request):
    return fsdict(tempfile.mktemp(), *request.param)


@pytest.fixture(params=itertools.product([PYTHON, JSON], [BunchDictionary], [LinkStorage, ReferenceStorage]))
def bunch_database(request):
    return fsdict(tempfile.mktemp(), *request.param)


def test_write_read_has_delete(database):
    # Make sure the database does not have the item
    assert "Hello" not in database

    # Write the Hello value
    database["Hello"] = "World"

    # Read the Hello value
    assert database["Hello"] == "World"

    # Make sure the database has the Hello item
    assert "Hello" in database

    # Delete the item
    del database["Hello"]

    # Make sure the database does not have the item
    assert "Hello" not in database

    # Make sure the getter now raises
    with pytest.raises(KeyError):
        assert database["Hello"] == "World"


def test_write_recursive_dicts(database):
    # Write the Hello value
    database["Hello"] = {"World": 42}

    # Read the Hello value
    assert database["Hello"] == dict(World=42)

    # Make sure the Hello value is a dictionary
    assert isinstance(database["Hello"], Dictionary)


def test_storage_usage(database):
    # Write the Hello value
    database["Hello"] = {"World": {"Another": "Value"}}

    # Make sure the storage usage is NOT zero
    assert os.listdir(database._key_storage._path)

    # Clear the database
    database.clear()

    # Make sure the database is empty
    assert len(database) == 0

    # Make sure the storage usage is zero
    assert not os.listdir(database._key_storage._path)


def test_bunch_write_read_has_delete(bunch_database):
    # Make sure the database does not have the attribute
    assert not hasattr(bunch_database, "hello_world")

    # Write to the database
    bunch_database.hello_world = "Hello World!"

    # Read the value and validate
    assert bunch_database.hello_world == "Hello World!"

    # Make sure the database has the attribute
    assert hasattr(bunch_database, "hello_world")

    # Delete the item
    del bunch_database.hello_world

    # Make sure the database does not have the attribute
    assert not hasattr(bunch_database, "hello_world")

    # Make sure a KeyError is raised
    with pytest.raises(KeyError):
        assert bunch_database.hello_world == "Hello World!"
