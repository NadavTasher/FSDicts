import os
import json

from puppy.database.types import AbstractMutableMapping, Mapping
from puppy.database.storage import Storage
from puppy.simple.filesystem import safe, remove

# Default encoding for text
_ENCODING = "utf-8"

# Content encoders
JSON = (json.dumps, json.loads)
Python = (repr, eval)


class Keystore(AbstractMutableMapping):

    # Initialize variables
    _path = None
    _encoding = None
    _keys, _values = None, None
    _encode, _decode = None, None

    def __init__(self, path, storages, encoder=JSON, encoding="utf-8"):
        # Make sure path exists
        if not os.path.exists(path):
            os.makedirs(path)

        # Set internal variables
        self._path = path
        self._keys, self._values = storages
        self._encode, self._decode = encoder
        self._encoding = encoding

    def _key_to_path(self, key):
        # Encode the key
        encoded_key = self._encode(key).encode(self._encoding)

        # Create a storage object from the key
        with self._keys.object_from_value(encoded_key) as key_object:
            # Create a path for the digest
            return os.path.join(self._path, key_object.id)

    def _path_to_key(self, path):
        # Fetch object ID from path name
        object_id = os.path.basename(path)

        # Open the object for reading
        with self._keys.object_from_id(object_id) as value_object:
            # Decode the object's value
            return self._decode(value_object.value.decode(self._encoding))

    def __getitem__(self, key):
        # Make sure key exists
        if key not in self:
            raise KeyError(key)

        # Resolve path of object
        path = self._key_to_path(key)

        # Check if object is a simple object
        if os.path.isfile(path):
            # Read the object ID
            with open(path, "r") as file:
                object_id = file.read()

            # Read the object value
            with self._values.object_from_id(object_id) as value_object:
                # Decode the value
                return self._decode(value_object.value.decode(self._encoding))
        else:
            # Create a keystore from the path
            return Keystore(path, (self._keys, self._values), (self._encode, self._decode), self._encoding)

    def __setitem__(self, key, value):
        # Delete the old value
        if key in self:
            del self[key]

        # Find the path to the key
        path = self._key_to_path(key)

        # Encode the key and value
        encoded_key = self._encode(key).encode(self._encoding)
        encoded_value = self._encode(value).encode(self._encoding)

        # Encode the path
        encoded_path = path.encode(self._encoding)

        # Add path to key storage
        with self._keys.object_from_value(encoded_key) as key_object:
            # Add the reference to the object
            key_object.register(encoded_path)

        # Check if value is a dictionary
        if not isinstance(value, Mapping):
            # Write the object and add a reference
            with self._values.object_from_value(encoded_value) as value_object:
                # Add the reference to the object
                value_object.register(encoded_path)

                # Write the object's ID
                with safe(path, "w") as file:
                    file.write(value_object.id)
        else:
            # Create a new keystore
            Keystore(path, (self._keys, self._values), (self._encode, self._decode), self._encoding).update(value)

    def __delitem__(self, key):
        # Find the path to the key
        path = self._key_to_path(key)

        # Encode the key and value
        encoded_key = self._encode(key).encode(_ENCODING)

        # Encode the path
        encoded_path = path.encode(_ENCODING)

        # Remove the reference for the key
        with self._keys.object_from_value(encoded_key) as key_object:
            key_object.unregister(encoded_path)

        # Check whether the path is a file or a directory
        if os.path.isfile(path):
            # Open the path for reading
            with open(path, "r") as file:
                object_id = file.read()

            # Remove a reference from the object
            with self._values.object_from_id(object_id) as value_object:
                value_object.unregister(encoded_path)
        else:
            # Create the keystore object and clear it
            Keystore(path, (self._keys, self._values), (self._encode, self._decode), self._encoding).clear()

        # Remove the path
        remove(path)

    def __contains__(self, key):
        # Check if file exists
        return os.path.exists(self._key_to_path(key))

    def __iter__(self):
        # List all of the items in the path
        for name in os.listdir(self._path):
            # Make sure checksum is not a temporary path
            if "~" in name:
                continue

            # Yield name for further usage
            yield self._path_to_key(name)

    def __len__(self):
        # Count all non-temporary names
        return len([name for name in os.listdir(self._path) if "~" not in name])


class Database(Keystore):

    def __init__(self, path, encoder=JSON):
        # Create the directory
        if not os.path.exists(path):
            os.makedirs(path)

        # Initialize the storage object
        storage = Storage(os.path.join(path, "hashes"))

        # Initialize the keystore with objects path and a rainbow table
        super(Database, self).__init__(os.path.join(path, "objects"), (storage, storage), encoder)

class FSDict(Keystore):

    def __init__(self, path, encoder, *dictionaries, **values):
        # Create the directory
        if not os.path.exists(path):
            os.makedirs(path)

        # Initialize the storage object
        storage = Storage(os.path.join(path, "hashes"))

        # Initialize the keystore with objects path and a rainbow table
        super(Database, self).__init__(os.path.join(path, "objects"), (storage, storage), encoder)