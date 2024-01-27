import os
import hashlib

from fsdicts.lock import Lock, RLock
from fsdicts.bunch import MutableAttributeMapping
from fsdicts.mapping import AdvancedMutableMapping, Mapping

# Create key and value prefixes
FILE_KEY = "key"
FILE_VALUE = "value"

# Create default object so that None can be used as default value
DEFAULT = object()


class Dictionary(AdvancedMutableMapping):

    def __init__(self, path, storage, encoder):
        # Make the path absolute
        path = os.path.abspath(path)

        # Create internal lock
        self._lock = Lock(path)
        self._mutex = RLock(self._lock)

        # Set internal variables
        self._path = path
        self._encode, self._decode = encoder
        self._key_storage, self._value_storage = storage

        # Make sure path exists
        if not os.path.exists(self._path):
            os.makedirs(self._path)

    def _item_path(self, key):
        # Hash the key using hashlib
        checksum = hashlib.md5(self._encode(key)).hexdigest()

        # Create both paths
        return os.path.join(self._path, checksum)

    def _child_instance(self, path):
        return Dictionary(path, (self._key_storage, self._value_storage), (self._encode, self._decode))

    def __getitem__(self, key):
        # Lock the mutex
        with self._mutex:
            # Make sure key exists
            if key not in self:
                raise KeyError(key)

            # Resolve item path
            item_path = self._item_path(key)

            # Resolve value path
            value_path = os.path.join(item_path, FILE_VALUE)

            # Check if object is a simple object
            if os.path.isdir(value_path):
                # Create a keystore from the path
                return self._child_instance(value_path)
            else:
                # Read the value, decode and return
                return self._decode(self._value_storage.readlink(value_path))

    def __setitem__(self, key, value):
        # Lock the mutex
        with self._mutex:
            # Delete the old value
            if key in self:
                del self[key]

            # Resolve item path
            item_path = self._item_path(key)

            # Create the item path
            os.makedirs(item_path)

            # Resolve value path
            key_path, value_path = os.path.join(item_path, FILE_KEY), os.path.join(item_path, FILE_VALUE)

            # Store the key in the object storage
            key_identifier = self._key_storage.put(self._encode(key))

            # Link the key to the translation
            self._key_storage.link(key_identifier, key_path)

            # Check if value is a dictionary
            if isinstance(value, Mapping):
                # Create the sub-dictionary
                dictionary = self._child_instance(value_path)

                # Update the dictionary with the values
                dictionary.update(value)
            else:
                # Store the value in the object storage
                value_identifier = self._value_storage.put(self._encode(value))

                # Link the value to the translation
                self._value_storage.link(value_identifier, value_path)

    def __delitem__(self, key):
        # Lock the mutex
        with self._mutex:
            # Make sure key exists
            if key not in self:
                raise KeyError(key)

            # Resolve item path
            item_path = self._item_path(key)

            # Resolve value path
            key_path, value_path = os.path.join(item_path, FILE_KEY), os.path.join(item_path, FILE_VALUE)

            # Unlink the key object
            self._key_storage.unlink(key_path)

            # If the value is a dictionary, clear the dictionary
            if os.path.isdir(value_path):
                # Create the dictionary
                dictionary = self._child_instance(value_path)

                # Clear the dictionary
                dictionary.clear()

                # Delete the directory - should be empty
                os.rmdir(value_path)
            else:
                # Unlink the value object
                self._value_storage.unlink(value_path)

            # Remove the item path
            os.rmdir(item_path)

    def __contains__(self, key):
        # Resolve item path
        item_path = self._item_path(key)

        # Check if paths exist
        return os.path.isdir(item_path)

    def __iter__(self):
        # List all of the items in the path
        for checksum in os.listdir(self._path):
            # Create key path
            key_path = os.path.join(self._path, checksum, FILE_KEY)

            # Read the key contents, decode and yield
            yield self._decode(self._key_storage.readlink(key_path))

    def __len__(self):
        # Count all key files
        return len(os.listdir(self._path))

    def __repr__(self):
        # Format the data like a dictionary
        return "{%s}" % ", ".join("%r: %r" % item for item in self.items())

    def __eq__(self, other):
        # Make sure the other object is a mapping
        if not isinstance(other, Mapping):
            return False

        # Make sure all keys exist
        if set(self.keys()) != set(other.keys()):
            return False

        # Make sure all the values equal
        for key in self:
            if self[key] != other[key]:
                return False

        # Comparison succeeded
        return True

    def clear(self):
        # Lock the mutex
        with self._mutex:
            # Loop over keys
            for key in self:
                # Delete the item
                del self[key]

    def pop(self, key, default=DEFAULT):
        try:
            # Lock the mutex
            with self._mutex:
                # Fetch the value
                value = self[key]

                # Check if the value is a keystore
                if isinstance(value, Mapping):
                    value = value.copy()

                # Delete the item
                del self[key]

                # Return the value
                return value
        except KeyError:
            # Check if a default is defined
            if default != DEFAULT:
                return default

            # Reraise exception
            raise

    def popitem(self):
        # Lock the mutex
        with self._mutex:
            # Convert self to list
            keys = list(self)

            # If the list is empty, raise
            if not keys:
                raise KeyError()

            # Pop a key from the list
            key = keys.pop()

            # Return the key and the value
            return key, self.pop(key)

    def copy(self):
        # Create initial bunch
        output = dict()

        # Loop over keys
        for key in self:
            # Fetch value of key
            value = self[key]

            # Check if value is a keystore
            if isinstance(value, Mapping):
                value = value.copy()

            # Update the bunch
            output[key] = value

        # Return the created output
        return output


class AttributeDictionary(Dictionary, MutableAttributeMapping):

    _path = None
    _lock, _mutex = None, None
    _encode, _decode = None, None
    _key_storage, _value_storage = None, None

    def _child_instance(self, path):
        return AttributeDictionary(path, (self._key_storage, self._value_storage), (self._encode, self._decode))
