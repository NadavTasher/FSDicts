import os
import hashlib
import binascii

from fsdicts.lock import TemporaryLock, DirectoryLock


class Storage(object):

    def __init__(self, path, lock):
        raise NotImplementedError()

    def put(self, value, link=None):
        raise NotImplementedError()

    def islink(self, link):
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


class NoStorage(Storage):

    def __init__(self, *args, **kwargs):
        # Initialize a counter
        self._counter = 0

    def put(self, value, link=None):
        # Link the value if needed
        if link:
            self.link(value, link)

        # Increment the counter
        self._counter += 1

        # Return the value as the identifier
        return value

    def islink(self, link):
        return os.path.isfile(link)

    def readlink(self, link):
        # Read the file
        with open(link, "rb") as file:
            return file.read()

    def link(self, identifier, link):
        # Write the identifier (value) to the link
        with open(link, "wb") as file:
            file.write(identifier)

    def unlink(self, link):
        # Remove the file
        os.remove(link)

    def release(self, identifier):
        # Decrement the counter
        self._counter -= 1

    def purge(self):
        # Reset the counter
        self._counter = 0

    def __len__(self):
        return self._counter


class LinkStorage(Storage):

    def __init__(self, path, lock=TemporaryLock, hash=hashlib.md5):
        # Make sure the operating system is supported
        if os.name != "posix":
            raise NotImplementedError("Unsupported operating system")

        # Make the path absolute
        path = os.path.abspath(path)

        # Intialize the path and hash
        self._path = path
        self._lock = lock
        self._hash = hash

        # Create the path if needed
        if not os.path.exists(self._path):
            os.makedirs(self._path)

    def _internal_link(self, identifier, link):
        # Link the identifier and the link
        os.link(identifier, link)

    def _internal_release(self, identifier):
        # Make sure the path exists
        if not os.path.isfile(identifier):
            raise ValueError(identifier)

        # If more then one link exists, skip
        if os.stat(identifier).st_nlink > 1:
            return

        # Remove the file
        os.remove(identifier)

    def put(self, value, link=None):
        # Create the value hash
        hash = self._hash(value).hexdigest()

        # Create the object path
        path = os.path.join(self._path, hash)

        # Lock the path
        with self._lock(path):
            # Write file if missing
            if not os.path.isfile(path):
                # Create temporary path for writing
                temporary = path + "." + binascii.b2a_hex(os.urandom(4)).decode()

                # Write the object
                with open(temporary, "wb") as object:
                    object.write(value)

                # Rename the temporary file
                os.rename(temporary, path)

            # Link as needed
            if link:
                self._internal_link(path, link)

        # Return the hash
        return path

    def islink(self, link):
        # Check whether the file exists
        return os.path.isfile(link)

    def readlink(self, link):
        # Read the identifier as a file
        with open(link, "rb") as object:
            value = object.read()

        # Return the value
        return value

    def link(self, identifier, link):
        # Lock the identifier
        with self._lock(identifier):
            # Link the identifier and the link
            return self._internal_link(identifier, link)

    def unlink(self, link):
        # Check whether the path exists
        if not os.path.isfile(link):
            raise ValueError(link)

        # Read the link and create hash
        with open(link, "rb") as object:
            object_value = object.read()

        # Create object hash
        object_hash = self._hash(object_value).hexdigest()

        # Create object path
        identifier = os.path.join(self._path, object_hash)

        # Lock the identifier
        with self._lock(identifier):
            # Remove the link
            os.unlink(link)

            # Clean the identifier
            self._internal_release(identifier)

    def release(self, identifier):
        # Lock the identifier
        with self._lock(identifier):
            return self._internal_release(identifier)

    def purge(self):
        # List all files in the storage and check the link count
        for hash in self:
            # Create the file path
            identifier = os.path.join(self._path, hash)

            # Lock the identifier
            with self._lock(identifier):
                # If path does not exist, skip
                if not os.path.isfile(identifier):
                    continue

                # Clean the file
                self._internal_release(identifier)

    def __iter__(self):
        # Calculate the checksum length
        length = len(self._hash().hexdigest())

        # Loop over object directory
        for hash in os.listdir(self._path):
            # Make sure hash matches expected length
            if len(hash) != length:
                continue

            # Yield the hash
            yield hash

    def __len__(self):
        # Count the object files
        return len(list(iter(self)))


class ReferenceStorage(Storage):

    def __init__(self, path, lock=DirectoryLock, hash=hashlib.md5):
        # Make the path absolute
        path = os.path.abspath(path)

        # Intialize the path and hash
        self._lock = lock
        self._hash = hash

        # Create the objects path and references path
        self._objects_path = os.path.join(path, "objects")
        self._references_path = os.path.join(path, "references")

        # Create the objects directory if needed
        if not os.path.isdir(self._objects_path):
            os.makedirs(self._objects_path)

        # Create the references directory if needed
        if not os.path.isdir(self._references_path):
            os.makedirs(self._references_path)

    def _internal_link(self, hash, link):
        # Create the object path
        object_path = os.path.join(self._objects_path, hash)

        # Make sure the object exists
        if not os.path.isfile(object_path):
            raise KeyError(hash)

        # Create references file path
        references_path = os.path.join(self._references_path, hash)

        # Append the path to the file
        with open(references_path, "a") as references_file:
            references_file.write(link + "\n")

        # Write the link file
        with open(link, "w") as file:
            file.write(hash)

    def _internal_release(self, hash):
        # Create the object path
        object_path = os.path.join(self._objects_path, hash)

        # Make sure the object exists
        if not os.path.isfile(object_path):
            raise KeyError(hash)

        # Create references file path
        references_path = os.path.join(self._references_path, hash)

        # If the references path exists, check references
        if os.path.isfile(references_path):
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

    def put(self, value, link=None):
        # Create the value hash
        hash = self._hash(value).hexdigest()

        # Create the object path
        object_path = os.path.join(self._objects_path, hash)

        # Lock the object
        with self._lock(object_path):
            # Check whether the path exists
            if not os.path.isfile(object_path):
                # Create temporary path for writing
                temporary = object_path + "." + binascii.b2a_hex(os.urandom(4)).decode()

                # Write the object
                with open(temporary, "wb") as object:
                    object.write(value)

                # Rename the temporary file
                os.rename(temporary, object_path)

            # Link if needed
            if link:
                self._internal_link(hash, link)

        # Return the hash
        return hash

    def islink(self, link):
        # If the file does not exist, not a valid link
        if not os.path.isfile(link):
            return False

        # If the file is empty, not a valid link
        if not os.path.getsize(link):
            return False

        # Valid link
        return True

    def readlink(self, link):
        # Read the link file
        with open(link, "r") as file:
            hash = file.read()

        # Calculate the checksum length
        length = len(self._hash().hexdigest())

        # Make sure the hash is valid
        if len(hash) != length:
            raise ValueError(hash)

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

        # Lock the object
        with self._lock(object_path):
            return self._internal_link(hash, link)

    def unlink(self, link):
        # Check whether the link is valid
        if not self.islink(link) and os.path.isfile(link):
            # Remove the link
            os.remove(link)

            # Nothing more to do
            return

        # Read the link file
        with open(link, "r") as file:
            hash = file.read()

        # Create the object path
        object_path = os.path.join(self._objects_path, hash)

        # Make sure the object exists
        if not os.path.isfile(object_path):
            raise KeyError(hash)

        # Lock the object
        with self._lock(object_path):
            # Create references file path
            references_path = os.path.join(self._references_path, hash)

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
            self._internal_release(hash)

    def release(self, hash):
        # Create the object path
        object_path = os.path.join(self._objects_path, hash)

        # Lock the object path
        with self._lock(object_path):
            return self._internal_release(hash)

    def purge(self):
        # List all objects in storage
        for hash in self:
            # Release the object
            self.release(hash)

    def __iter__(self):
        # Calculate the checksum length
        length = len(self._hash().hexdigest())

        # Loop over object directory
        for hash in os.listdir(self._objects_path):
            # Make sure hash matches expected length
            if len(hash) != length:
                continue

            # Yield the hash
            yield hash

    def __len__(self):
        # Count the object files
        return len(list(iter(self)))
