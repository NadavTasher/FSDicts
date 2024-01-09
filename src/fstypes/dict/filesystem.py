import os
import shutil
import contextlib

from fstypes.dict.mapping import AbstractMutableMapping


class FileSystemMutableMapping(AbstractMutableMapping):

    # Initialize variables
    _path = None

    def __init__(self, path):
        # Create directories if they do not exist
        if not os.path.exists(path):
            os.makedirs(path)

        # Set internal parameters
        self._path = path

    def _key_to_path(self, key):
        # Join the path with the key name
        return os.path.join(self._path, key)

    def _path_to_key(self, path):
        # Convert the path to a basename
        return os.path.basename(path)

    def __getitem__(self, key):
        # Make sure key exists
        if key not in self:
            raise KeyError(key)

        # Read file contents
        with open(self._key_to_path(key), "rb") as file:
            return file.read()

    def __setitem__(self, key, value):
        # Make sure the key is a valid path
        if key != os.path.basename(key):
            raise TypeError(key)

        # Make sure the value is bytes
        if not isinstance(value, bytes):
            raise TypeError(value)

        # Write the object data as string
        with safe(self._key_to_path(key), "wb") as file:
            file.write(value)

    def __delitem__(self, key):
        # Make sure key exists
        if key not in self:
            raise KeyError(key)

        # Remove the path
        remove(self._key_to_path(key))

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
