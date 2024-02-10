import os

from fsdicts.lock import TimeoutLock, TemporaryLock
from fsdicts.encoders import JSON, PYTHON
from fsdicts.storage import ReferenceStorage, LinkStorage
from fsdicts.dictionary import AttributeDictionary


def fsdict(path, encoder=JSON, dictionary=AttributeDictionary, storage=ReferenceStorage, lock=TimeoutLock):
    # Create the directory
    if not os.path.exists(path):
        os.makedirs(path)

    # Initialize the storage object
    key_storage = storage(os.path.join(path, "keys"), lock=lock)
    value_storage = storage(os.path.join(path, "values"), lock=lock)

    # Initialize the keystore with objects path and a rainbow table
    return dictionary(os.path.join(path, "structure"), (key_storage, value_storage), encoder, lock)


def localdict(path, encoder=PYTHON):
    # Pick the best locks and storage for use-case
    if os.name == "posix":
        return fsdict(path, encoder=encoder, dictionary=AttributeDictionary, storage=LinkStorage, lock=TemporaryLock)
    else:
        return fsdict(path, encoder=encoder, dictionary=AttributeDictionary, storage=ReferenceStorage, lock=TemporaryLock)
