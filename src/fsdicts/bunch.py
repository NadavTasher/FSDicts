from fsdicts.mapping import MutableMapping, Mapping


class AttributeMapping(Mapping):

    def __getattr__(self, key):
        try:
            return object.__getattribute__(self, key)
        except AttributeError:
            # Key is not in prototype chain, try returning
            try:
                return self[key]
            except KeyError:
                # Replace KeyErrors with AttributeErrors
                raise AttributeError(key)


class MutableAttributeMapping(MutableMapping, AttributeMapping):

    def __setattr__(self, key, value):
        try:
            object.__getattribute__(self, key)
        except AttributeError:
            # Convert value to bunch
            if isinstance(value, Mapping):
                value = Bunch(value)

            # Set the item
            self[key] = value
        else:
            # Key is in prototype chain, set it
            object.__setattr__(self, key, value)

    def __delattr__(self, key):
        try:
            object.__getattribute__(self, key)
        except AttributeError:
            # Delete the item
            try:
                del self[key]
            except KeyError:
                # Replace KeyErrors with AttributeErrors
                raise AttributeError(key)
        else:
            # Key is in prototype chain, delete it
            object.__delattr__(self, key)


class Bunch(dict, MutableAttributeMapping):
    pass
