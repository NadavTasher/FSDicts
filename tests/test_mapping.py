import json
import pytest

from fsdicts import *


def test_setdefaults():
    # Create test type
    class AdvancedBunch(Bunch, AdvancedMutableMapping):
        pass

    # Create a bunch
    bunch = AdvancedBunch(hello="World")
    bunch.setdefaults(hello="Changed!", world="Good")

    # Check values
    assert bunch.hello == "World"
    assert bunch.world == "Good"


def test_json_encoding():
    # Create a test class that imitates a mapping
    class MyMapping(Mapping):

        def __getitem__(self, key):
            return "World"

        def __len__(self):
            return 1

        def __iter__(self):
            return iter(["Hello"])

        def copy(self):
            return {key: self[key] for key in self}

    # Create a test object
    my_mapping = MyMapping()

    # Try encoding the mapping
    assert json.dumps(my_mapping) == '{"Hello": "World"}'
