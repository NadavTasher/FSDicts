import json
import functools

try:
    # Python 3 mapping
    from collections.abc import MutableMapping, Mapping
except:
    # Python 2 mapping
    from collections import MutableMapping, Mapping

# Default value to use instead of None, when None can be used as a value
DEFAULT = object()


class AdvancedMutableMapping(MutableMapping):

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
        output = Bunch()

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

    def setdefaults(self, *dictionaries, **values):
        # Update values to include all dicts
        for dictionary in dictionaries:
            values.update(dictionary)

        # Loop over all items and set the default value
        for key, value in values.items():
            self.setdefault(key, value)


class Encoder(json.JSONEncoder):

    def default(self, obj):
        # Check if the object is a keystore
        if isinstance(obj, Mapping):
            # Return a JSON encodable representation of the keystore
            return obj.copy()

        # Fallback default
        return super(Encoder, self).default(obj)


# Update the default dumps function
json.dump = functools.partial(json.dump, cls=Encoder)
json.dumps = functools.partial(json.dumps, cls=Encoder)
