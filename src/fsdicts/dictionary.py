import os
import hashlib

from fsdicts.bunch import MutableAttributeMapping
from fsdicts.mapping import AdvancedMutableMapping, Mapping

# Create key and value prefixes
FILE_KEY = "key"
FILE_VALUE = "value"

# Create default object so that None can be used as default value
DEFAULT = object()


class Dictionary(AdvancedMutableMapping):

    def __init__(self, path, storage, encoder, lock):
        # Make the path absolute
        path = os.path.abspath(path)

        # Set internal lock class
        self._lock = lock

        # Set internal variables
        self._path = path
        self._encode, self._decode = encoder
        self._key_storage, self._value_storage = storage

        # Make sure path exists
        if not os.path.exists(self._path):
            os.makedirs(self._path)

    def _child_instance(self, path):
        return Dictionary(path, (self._key_storage, self._value_storage), (self._encode, self._decode), self._lock)

    def _internal_iterate(self):
        # List all of the items in the path
        for checksum in os.listdir(self._path):
            # Create item path
            item_path = os.path.join(self._path, checksum)

            # Make sure the item is valid
            if not self._internal_has(item_path):
                continue

            # Yield the checksum
            yield item_path

    def _internal_has(self, item_path):
        # Resolve value path
        key_path, value_path = os.path.join(item_path, FILE_KEY), os.path.join(item_path, FILE_VALUE)

        # Make sure the key path exists and is a valid link
        if not self._key_storage.islink(key_path):
            return False

        # Make sure the value path exists
        if not os.path.exists(value_path):
            return False

        # If the value path is a file, should also be a link
        if os.path.isfile(value_path):
            if not self._value_storage.islink(value_path):
                return False

        # Check if paths exist
        return os.path.isdir(item_path)

    def _internal_set(self, key, value):
        # Resolve item path
        item_path = self._item_path(key)

        # Delete the old value
        if self._internal_has(item_path):
            self._internal_delete(key)

        # Create the item path
        os.makedirs(item_path)

        # Resolve value path
        key_path, value_path = os.path.join(item_path, FILE_KEY), os.path.join(item_path, FILE_VALUE)

        # Store the key in the object storage
        self._key_storage.put(self._encode(key), key_path)

        # Check if value is a dictionary
        if isinstance(value, Mapping):
            # Create the sub-dictionary
            dictionary = self._child_instance(value_path)

            # Update the dictionary with the values
            dictionary.update(value)
        else:
            # Store the value in the object storage
            self._value_storage.put(self._encode(value), value_path)

    def _internal_get(self, key):
        # Resolve item path
        item_path = self._item_path(key)

        # Make sure key exists
        if not self._internal_has(item_path):
            raise KeyError(key)

        # Resolve value path
        value_path = os.path.join(item_path, FILE_VALUE)

        # Check if object is a simple object
        if os.path.isdir(value_path):
            # Create a keystore from the path
            return self._child_instance(value_path)
        else:
            # Read the value, decode and return
            return self._decode(self._value_storage.readlink(value_path))

    def _internal_delete(self, key):
        # Resolve item path
        item_path = self._item_path(key)

        # Make sure key exists
        if not self._internal_has(item_path):
            raise KeyError(key)

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

    def _item_path(self, key):
        # Hash the key using hashlib
        checksum = hashlib.md5(self._encode(key)).hexdigest()

        # Create both paths
        return os.path.join(self._path, checksum)

    def __getitem__(self, key):
        # Resolve item path
        item_path = self._item_path(key)

        # Lock the item for modifications
        with self._lock(item_path):
            return self._internal_get(key)

    def __setitem__(self, key, value):
        # Resolve item path
        item_path = self._item_path(key)

        # Lock the item for modifications
        with self._lock(item_path):
            return self._internal_set(key, value)

    def __delitem__(self, key):
        # Resolve item path
        item_path = self._item_path(key)

        # Lock the item for modifications
        with self._lock(item_path):
            return self._internal_delete(key)

    def __contains__(self, key):
        # Resolve item path
        item_path = self._item_path(key)

        # Check if paths exist
        with self._lock(item_path):
            return self._internal_has(item_path)

    def __iter__(self):
        # List all of the items in the path
        for item_path in self._internal_iterate():
            # Read the key contents and decode
            with self._lock(item_path):
                key_contents = self._decode(self._key_storage.readlink(os.path.join(item_path, FILE_KEY)))

            # Yield the key contents
            yield key_contents

    def __len__(self):
        # Count all key files
        return len(list(self._internal_iterate()))

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

    def pop(self, key, default=DEFAULT):
        try:
            # Resolve item path
            item_path = self._item_path(key)

            # Check if paths exist
            with self._lock(item_path):
                # Fetch the value
                value = self._internal_get(key)

                # Check if the value is a keystore
                if isinstance(value, Mapping):
                    value = value.copy()

                # Delete the item
                self._internal_delete(key)

            # Return the value
            return value
        except KeyError:
            # Check if a default is defined
            if default != DEFAULT:
                return default

            # Reraise exception
            raise

    def popitem(self):
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

    def clear(self):
        # Loop over keys
        for key in self:
            # Delete the item
            del self[key]


class AttributeDictionary(Dictionary, MutableAttributeMapping):

    _lock = None
    _path = None
    _encode, _decode = None, None
    _key_storage, _value_storage = None, None

    def _child_instance(self, path):
        return AttributeDictionary(path, (self._key_storage, self._value_storage), (self._encode, self._decode), self._lock)
