import os
import hashlib

from fsdicts.bunch import MutableAttributeMapping
from fsdicts.mapping import AdvancedMutableMapping, Mapping

# Create key and value prefixes
PREFIX_KEY = "key-"
PREFIX_VALUE = "value-"

# Create default object so that None can be used as default value
DEFAULT = object()


class Dictionary(AdvancedMutableMapping):

    def __init__(self, path, storage, encoder):
        # Make the path absolute
        path = os.path.abspath(path)

        # Set internal variables
        self._path = path
        self._encode, self._decode = encoder
        self._key_storage, self._value_storage = storage

        # Make sure path exists
        if not os.path.exists(self._path):
            os.makedirs(self._path)

    def _resolve_key(self, key):
        # Hash the key using hashlib
        checksum = hashlib.md5(self._encode(key)).hexdigest()

        # Create both paths
        return os.path.join(self._path, PREFIX_KEY + checksum), os.path.join(self._path, PREFIX_VALUE + checksum)

    def _child_instance(self, path):
        return Dictionary(path, (self._key_storage, self._value_storage), (self._encode, self._decode))

    def __getitem__(self, key):
        # Make sure key exists
        if key not in self:
            raise KeyError(key)

        # Resolve key and value paths
        _, value_path = self._resolve_key(key)

        # Check if object is a simple object
        if os.path.isdir(value_path):
            # Create a keystore from the path
            return self._child_instance(value_path)

        # Read the object value
        encoded_value = self._value_storage.readlink(value_path)

        # Decode the value
        return self._decode(encoded_value)

    def __setitem__(self, key, value):
        # Delete the old value
        if key in self:
            del self[key]

        # Create the key and value paths
        key_path, value_path = self._resolve_key(key)

        # Encode the key
        encoded_key = self._encode(key)

        # Store the key in the object storage
        key_identifier = self._key_storage.put(encoded_key)

        # Link the key to the translation
        self._key_storage.link(key_identifier, key_path)

        # Check if value is a dictionary
        if isinstance(value, Mapping):
            # Create the sub-dictionary
            dictionary = self._child_instance(value_path)

            # Update the dictionary with the values
            dictionary.update(value)

            # Return - nothing more to do
            return

        # Encode the value
        encoded_value = self._encode(value)

        # Store the value in the object storage
        value_identifier = self._value_storage.put(encoded_value)

        # Link the value to the translation
        self._value_storage.link(value_identifier, value_path)

    def __delitem__(self, key):
        # Make sure key exists
        if key not in self:
            raise KeyError(key)

        # Resolve key and value paths
        key_path, value_path = self._resolve_key(key)

        # Release the key object
        self._key_storage.unlink(key_path)

        # If the value is a dictionary, clear the dictionary
        if os.path.isdir(value_path):
            # Create the dictionary
            dictionary = self._child_instance(value_path)

            # Clear the dictionary
            dictionary.clear()

            # Delete the directory - should be empty
            os.rmdir(value_path)

            # Return - nothing more to do
            return

        # Release the value object
        self._value_storage.unlink(value_path)

    def __contains__(self, key):
        # Resolve key and value paths
        key_path, value_path = self._resolve_key(key)

        # Check if paths exist
        return os.path.exists(key_path) and os.path.exists(value_path)

    def __iter__(self):
        # List all of the items in the path
        for name in os.listdir(self._path):
            # Make sure name starts with key prefix
            if not name.startswith(PREFIX_KEY):
                continue

            # Create key path
            key_path = os.path.join(self._path, name)

            # Read the key contents
            encoded_key = self._key_storage.readlink(key_path)

            # Decode the key and yield
            yield self._decode(encoded_key)

    def __len__(self):
        # Count all key files
        return len(list(filter(lambda name: name.startswith(PREFIX_KEY), os.listdir(self._path))))

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

    _path = None
    _encode, _decode = None, None
    _key_storage, _value_storage = None, None

    def _child_instance(self, path):
        return AttributeDictionary(path, (self._key_storage, self._value_storage), (self._encode, self._decode))
