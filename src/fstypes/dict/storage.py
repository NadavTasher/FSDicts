import os
import hashlib

from fstypes.dict.filesystem import FileSystemMutableMapping


class Storage(object):

    def __init__(self, path):
        # Make sure the path exists
        if not os.path.exists(path):
            os.makedirs(path)

        # Create checksum calculator
        self._path = path

        # Create the objects dictionary
        self._objects_path = os.path.join(self._path, "objects")
        self._references_path = os.path.join(self._path, "references")

    def object_from_id(self, object_id):
        return Object(self._objects_path, self._references_path, object_id=object_id)

    def object_from_value(self, object_value):
        return Object(self._objects_path, self._references_path, object_value=object_value)


class Object(object):

    def __init__(self, objects_path, references_path, object_id=None, object_value=None):
        # Create objects dictionary
        self._objects = FileSystemMutableMapping(objects_path)

        # Make sure object ID or value are defined
        assert bool(object_id) != bool(object_value)

        # Set object ID and value
        self._id, self._value = object_id, object_value

        # Create references object
        self._references = FileSystemMutableMapping(os.path.join(references_path, self.id))

    @property
    def id(self):
        # Check whether the id is defined
        if not self._id:
            self._id = hashlib.sha256(self._value).hexdigest()

        # Return the ID
        return self._id

    @property
    def value(self):
        # Check whether the value is defined
        if not self._value:
            self._value = self._objects[self._id]

        # Validate the checksum
        if hashlib.sha256(self._value).hexdigest() != self.id:
            raise ValueError(self.id)

        # Return the ID
        return self._value

    def register(self, path):
        # Create a checksum for the reference
        checksum = hashlib.sha256(path).hexdigest()

        # Make sure the reference does not exist
        if checksum in self._references:
            return

        # Add the reference
        self._references[checksum] = path

    def unregister(self, path):
        # Create a checksum for the reference
        checksum = hashlib.sha256(path).hexdigest()

        # Make sure the reference does not exist
        if checksum not in self._references:
            raise KeyError(path)

        # Delete the reference checksum
        del self._references[checksum]

    def __enter__(self):
        # Return self for handling
        return self

    def __exit__(self, *exc_info):
        # Check whether object should exist
        if len(self._references):
            # Make sure object does not exist
            if self.id not in self._objects:
                # Write the object to the storage
                self._objects[self.id] = self.value
        else:
            # Make sure object exists
            if self.id in self._objects:
                # Delete the object
                del self._objects[self.id]

        # Return false for with statement
        return False
