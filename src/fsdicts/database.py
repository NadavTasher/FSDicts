import os

from fsdicts.encoders import JSON, PYTHON
from fsdicts.storage import ReferenceStorage, LinkStorage
from fsdicts.dictionary import AttributeDictionary


def fsdict(path, encoder=JSON, dictionary=AttributeDictionary, storage=ReferenceStorage):
    # Create the directory
    if not os.path.exists(path):
        os.makedirs(path)

    # Initialize the storage object
    key_storage = storage(os.path.join(path, "keys"))
    value_storage = storage(os.path.join(path, "values"))

    # Initialize the keystore with objects path and a rainbow table
    return dictionary(os.path.join(path, "structure"), (key_storage, value_storage), encoder)


def fastdict(path):
    # Make sure the operating system is supported
    assert os.name == "posix", "Unsupported operating system"

    # Create an attribute dict with link storage
    return fsdict(path, encoder=PYTHON, dictionary=AttributeDictionary, storage=LinkStorage)
