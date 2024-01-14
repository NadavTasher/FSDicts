import os
import hashlib
import binascii

from fsdicts.lock import Lock

DIRECTORY_OBJECTS = "objects"
DIRECTORY_REFERENCES = "references"


class Storage(object):

    def __init__(self, path):
        raise NotImplementedError()

    def put(self, value):
        raise NotImplementedError()

    def readlink(self, link):
        raise NotImplementedError()

    def link(self, identifier, link):
        raise NotImplementedError()

    def unlink(self, link):
        raise NotImplementedError()

    def release(self, identifier):
        raise NotImplementedError()

    def purge(self):
        raise NotImplementedError()

    def __len__(self):
        raise NotImplementedError()


class LinkStorage(Storage):

    def __init__(self, path, hash=hashlib.md5):
        # Make the path absolute
        path = os.path.abspath(path)

        # Intialize the path and hash
        self._path = path
        self._hash = hash

        # Create the path if needed
        if not os.path.exists(self._path):
            os.makedirs(self._path)

    def put(self, value):
        # Create the value hash
        hash = self._hash(value).hexdigest()

        # Create the object path
        path = os.path.join(self._path, hash)

        # Check whether the path exists
        if os.path.isfile(path):
            return path

        # Create temporary path for writing
        temporary = path + "." + binascii.b2a_hex(os.urandom(4)).decode()

        # Write the object
        with open(temporary, "wb") as object:
            object.write(value)

        # Rename the temporary file
        os.rename(temporary, path)

        # Return the hash
        return path

    def readlink(self, link):
        # Read the identifier as a file
        with open(link, "rb") as object:
            value = object.read()

        # Return the value
        return value

    def link(self, identifier, link):
        # Link the identifier and the link
        os.link(identifier, link)

    def unlink(self, link):
        # Check whether the path exists
        if not os.path.isfile(link):
            raise ValueError(link)

        # Read the link and create hash
        with open(link, "rb") as object:
            object_value = object.read()

        # Create object hash
        object_hash = self._hash(object_value).hexdigest()

        # Remove the link
        os.unlink(link)

        # Create object path
        path = os.path.join(self._path, object_hash)

        # Clean the path
        self.release(path)

    def release(self, identifier):
        # Make sure the path exists
        if not os.path.isfile(identifier):
            raise ValueError(identifier)

        # If more then one link exists, skip
        if os.stat(identifier).st_nlink > 1:
            return

        # Remove the file
        os.remove(identifier)

    def purge(self):
        # List all files in the storage and check the link count
        for hash in os.listdir(self._path):
            # Create the file path
            path = os.path.join(self._path, hash)

            # If path does not exist, skip
            if not os.path.isfile(path):
                continue

            # Clean the file
            self.release(path)

    def __len__(self):
        # Count the object files
        return len(os.listdir(self._path))


class ReferenceStorage(Storage):

    def __init__(self, path, hash=hashlib.md5):
        # Make the path absolute
        path = os.path.abspath(path)

        # Intialize the path and hash
        self._hash = hash

        # Create the objects path and references path
        self._objects_path = os.path.join(path, DIRECTORY_OBJECTS)
        self._references_path = os.path.join(path, DIRECTORY_REFERENCES)

        # Create the objects directory if needed
        if not os.path.isdir(self._objects_path):
            os.makedirs(self._objects_path)

        # Create the references directory if needed
        if not os.path.isdir(self._references_path):
            os.makedirs(self._references_path)

    def put(self, value):
        # Create the value hash
        hash = self._hash(value).hexdigest()

        # Create the object path
        object_path = os.path.join(self._objects_path, hash)

        # Check whether the path exists
        if os.path.isfile(object_path):
            return hash

        # Create temporary path for writing
        temporary = object_path + "." + binascii.b2a_hex(os.urandom(4)).decode()

        # Write the object
        with open(temporary, "wb") as object:
            object.write(value)

        # Rename the temporary file
        os.rename(temporary, object_path)

        # Return the hash
        return hash

    def readlink(self, link):
        # Read the link file
        with open(link, "r") as file:
            hash = file.read()

        # Create the object path
        object_path = os.path.join(self._objects_path, hash)

        # Make sure the object exists
        if not os.path.isfile(object_path):
            raise KeyError(hash)

        # Read the object file
        with open(object_path, "rb") as object:
            value = object.read()

        # Return the value
        return value

    def link(self, hash, link):
        # Create the object path
        object_path = os.path.join(self._objects_path, hash)

        # Make sure the object exists
        if not os.path.isfile(object_path):
            raise KeyError(hash)

        # Create references file path
        references_path = os.path.join(self._references_path, hash)

        # Lock the references
        with Lock(references_path):
            # Append the path to the file
            with open(references_path, "a") as references_file:
                references_file.write(link + "\n")

        # Write the link file
        with open(link, "w") as file:
            file.write(hash)

    def unlink(self, link):
        # Read the link file
        with open(link, "r") as file:
            hash = file.read()

        # Create the object path
        object_path = os.path.join(self._objects_path, hash)

        # Make sure the object exists
        if not os.path.isfile(object_path):
            raise KeyError(hash)

        # Create references file path
        references_path = os.path.join(self._references_path, hash)

        # Lock the references
        with Lock(references_path):
            # Read the list of references from the file
            with open(references_path, "r") as references_file:
                references = references_file.read().splitlines()

            # Filter out the current reference
            references = list(filter(lambda reference: reference != link, references))

            # Write the list of references back to the file
            with open(references_path, "w") as references_file:
                for reference in references:
                    references_file.write(reference + "\n")

        # Remove the link path
        os.remove(link)

        # Release the object
        self.release(hash)

    def release(self, hash):
        # Create the object path
        object_path = os.path.join(self._objects_path, hash)

        # Make sure the object exists
        if not os.path.isfile(object_path):
            return

        # Create references file path
        references_path = os.path.join(self._references_path, hash)

        # If the references path exists, check references
        if os.path.isfile(references_path):
            # Lock the references
            with Lock(references_path):
                # Read the list of references from the file
                with open(references_path, "r") as references_file:
                    references = references_file.read().splitlines()

                # Filter out references that do not exist
                references = list(filter(lambda reference: os.path.isfile(reference), references))

                # If there are references, return - can't purge
                if references:
                    return

                # Remove the references file
                os.remove(references_path)

        # Remove the object path
        os.remove(object_path)

    def purge(self):
        # List all objects in storage
        for hash in os.listdir(self._objects_path):
            # Release the object
            self.release(hash)

    def __len__(self):
        # Count the object files
        return len(os.listdir(self._objects_path))
