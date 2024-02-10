import pytest
import tempfile
import itertools

from fsdicts import *


@pytest.fixture(params=itertools.product([PYTHON, JSON], [Dictionary, AttributeDictionary], [LinkStorage, ReferenceStorage], [TemporaryLock, TimeoutLock]))
def database(request):
    return fsdict(tempfile.mktemp(), *request.param)


@pytest.fixture(params=itertools.product([PYTHON, JSON], [AttributeDictionary], [LinkStorage, ReferenceStorage], [TemporaryLock, DirectoryLock]))
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
    assert len(database._key_storage)

    # Clear the database
    database.clear()

    # Make sure the database is empty
    assert len(database) == 0

    # Make sure the storage usage is zero
    assert not len(database._key_storage)


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
    with pytest.raises(AttributeError):
        assert bunch_database.hello_world == "Hello World!"


def test_len(database):
    # Make sure database is empty
    assert not database

    # Load value to database
    database["Hello"] = "World"

    # Make sure database is not empty
    assert database


def test_pop(database):
    # Load value to database
    database["Hello"] = "World"

    # Pop the item from the database
    assert database.pop("Hello") == "World"

    # Make sure the database is empty
    assert not database


def test_popitem(database):
    # Load value to database
    database["Hello"] = "World"

    # Pop the item from the database
    assert database.popitem() == ("Hello", "World")

    # Make sure the database is empty
    assert not database


def test_copy(database):
    # Load values to database
    database["Hello1"] = "World1"
    database["Hello2"] = "World2"

    # Copy the database and compare
    copy = database.copy()

    # Check copy
    assert isinstance(copy, dict)
    assert copy == {"Hello1": "World1", "Hello2": "World2"}


def test_equals(database):
    # Load values to database
    database["Hello1"] = "World1"
    database["Hello2"] = "World2"

    assert database == {"Hello1": "World1", "Hello2": "World2"}
    assert database != {"Hello1": "World1", "Hello2": "World2", "Hello3": "World3"}
    assert database != {"Hello2": "World2", "Hello3": "World3"}


def test_representation(database):
    # Make sure looks good empty
    assert repr(database) == "{}"

    # Load some values
    database["Hello"] = "World"
    database["Other"] = {"Test": 1}

    # Make sure looks good with data
    assert repr(database) in ["{'Hello': 'World', 'Other': {'Test': 1}}", "{'Other': {'Test': 1}, 'Hello': 'World'}"] + ["{u'Hello': u'World', u'Other': {u'Test': 1}}", "{u'Other': {u'Test': 1}, u'Hello': u'World'}"]


def test_clear(database):
    # Load some values
    database["Hello"] = "World"
    database["Other"] = {"Test": 1}

    # Fetch other database
    other = database["Other"]

    # Make sure other is not empty
    assert other

    # Clear the database
    database.clear()

    # Make sure database is empty
    assert not database

    # Make sure other does not exist
    with pytest.raises(OSError):
        assert not other
