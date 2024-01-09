import os

class Manager(object):

    def __init__(self, path, hash, jump=2, depth=3):
        # Initialize the path and the hash
        self._path = path
        self._hash = hash
        self._jump = jump
        self._depth = depth

        # Create the directory if needed
        if not os.path.isdir(path):
            os.makedirs(path)

    def has_value(self, hash):
        pass

    def read_value(self, hash):
        pass

    def write_value(self, value):
        pass