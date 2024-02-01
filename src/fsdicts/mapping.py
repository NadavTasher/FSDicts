import json
import functools

try:
    # Python 3 mapping
    from collections.abc import MutableMapping, Mapping
except:
    # Python 2 mapping
    from collections import MutableMapping, Mapping


class AdvancedMutableMapping(MutableMapping):

    def setdefaults(self, *dictionaries, **values):
        # Update values to include all dicts
        for dictionary in dictionaries:
            values.update(dictionary)

        # Loop over all items and set the default value
        for key, value in values.items():
            self.setdefault(key, value)


class MappingEncoder(json.JSONEncoder):

    def default(self, obj):
        # Check if the object is a keystore
        if isinstance(obj, Mapping):
            # Return a JSON encodable representation of the keystore
            return obj.copy()

        # Fallback default
        return super(MappingEncoder, self).default(obj)


# Update the default dumps function
json.dump = functools.partial(json.dump, cls=MappingEncoder)
json.dumps = functools.partial(json.dumps, cls=MappingEncoder)
