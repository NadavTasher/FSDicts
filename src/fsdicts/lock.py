import os
import time
import random

# Create lock directory postfix
POSTFIX_LOCK = ".lock"


class Lock(object):

    def __init__(self, path):
        # Create the lock path
        self._path = path + POSTFIX_LOCK

        # Create internal state
        self._locked = False
        self._attempts = 0

    def locked(self):
        return self._locked

    def lock(self):
        # Loop until locked
        while not self._locked:
            try:
                # Try creating the directory
                os.mkdir(self._path)

                # Update the lock status
                self._locked = True
            except OSError:
                # Increment the attempts
                self._attempts += 1

                # Sleep random amount
                time.sleep(random.random() / 1000.0)

    def unlock(self):
        # Make sure not already unlocked
        if not self._locked:
            return

        # Try removing the directory
        os.rmdir(self._path)

        # Update the lock status
        self._locked = False
        self._attempts = 0

    def __enter__(self):
        # Lock the lock
        self.lock()

        # Return "self"
        return self

    def __exit__(self, *exc_info):
        # Unlock the lock
        self.unlock()

    def __str__(self):
        # Create a string representation of the lock
        return "<%s, %s, %d attempts>" % (self.__class__.__name__, "locked" if self._locked else "unlocked", self._attempts)