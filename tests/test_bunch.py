import pytest

from fsdicts.bunch import Bunch


def test_bunch():
    # Create a test bunch
    bunch = Bunch(hello="World")

    # Make sure it has the attribute
    assert hasattr(bunch, "hello")
    assert not hasattr(bunch, "World")

    # Write the World attribute using setitem
    bunch["World"] = "Hello"

    # Make sure the bunch has the attribute now
    assert hasattr(bunch, "World")

    # Make sure attributes can be deleted
    del bunch.World

    # Make sure the attribute does not exist
    assert not hasattr(bunch, "World")

    # Make sure the getter raises attribute error
    with pytest.raises(AttributeError):
        a = bunch.World

    # Make sure the getitem raised key error
    with pytest.raises(KeyError):
        b = bunch["World"]