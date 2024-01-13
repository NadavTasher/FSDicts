import os

from fsdicts.encoders import JSON
from fsdicts.storage import ReferenceStorage
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
