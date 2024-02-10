import os
import time
import shutil
import random
import hashlib
import tempfile
import threading

from fsdicts.encoders import ENCODING


class Lock(object):

    def __init__(self, path):
        # Set the path internally
        self._path = path

        # Create internal state
        self._locked = False

    def _try_acquire(self):
        raise NotImplementedError()

    def _try_release(self):
        raise NotImplementedError()

    def locked(self):
        return self._locked

    def acquire(self, blocking=True, timeout=None):
        # Mark start time
        start_time = time.time()

        # Try acquiring for the first time
        if self._try_acquire():
            return True

        # If non-blocking, return here
        if not blocking:
            return False

        # Loop until timeout is reached
        while (timeout is None) or (time.time() - start_time) < timeout:
            # Try aquiring the lock
            if self._try_acquire():
                return True

            # Sleep random amount
            time.sleep(random.random() / 1000.0)

        # Timeout reached
        return False

    def release(self):
        # Make sure not already unlocked
        if not self._locked:
            return

        # Try releasing the lock
        self._try_release()

    def __enter__(self):
        # Lock the lock
        self.acquire()

        # Return "self"
        return self

    def __exit__(self, *exc_info):
        # Unlock the lock
        self.release()

    def __str__(self):
        # Create a string representation of the lock
        return "<%s, %s>" % (self.__class__.__name__, "locked" if self._locked else "unlocked")


class DirectoryLock(Lock):

    def __init__(self, path):
        # Initialize the parent
        super(DirectoryLock, self).__init__(path + ".lock")

    def _try_acquire(self):
        try:
            # Try creating the file
            os.mkdir(self._path)

            # Update lock state
            self._locked = True

            # Locking succeeded
            return True
        except OSError:
            # Locking failed
            return False

    def _try_release(self):
        # Try removing the directory
        os.rmdir(self._path)

        # Update the lock status
        self._locked = False


class TimeoutLock(Lock):

    TIMEOUT = 60 * 10  # 10 Minutes

    def __init__(self, path, timeout=None):
        # Initialize the parent
        super(TimeoutLock, self).__init__(path + ".lock")

        # Set the internal timeout
        self._timeout = timeout or self.TIMEOUT

    def _try_acquire(self):
        try:
            # Try creating the file
            os.mkdir(self._path)

            # Update lock state
            self._locked = True

            # Locking succeeded
            return True
        except OSError:
            # Try clearing the lock
            self._try_clear()

            # Locking failed
            return False

    def _try_release(self):
        # Remove the directory
        shutil.rmtree(self._path, ignore_errors=True)

        # Set the lock state
        self._locked = False

    def _try_clear(self):
        try:
            # Check lock age to compare against timeout
            if (time.time() - os.path.getctime(self._path)) < self._timeout:
                # Lock is not old enough
                return False

            # Try releasing the lock
            self._try_release()

            # Lock was released
            return True
        except OSError:
            # Failed clearing lock
            return False


class TemporaryLock(TimeoutLock):

    DIRECTORY = os.path.join(tempfile.gettempdir(), __name__)

    def __init__(self, path, timeout=None):
        # Create the directory if it does not exist
        if not os.path.isdir(self.DIRECTORY):
            os.makedirs(self.DIRECTORY)

        # If the path is a string, encode it
        if isinstance(path, str):
            path = path.encode(ENCODING)

        # Create hexdigest from path
        hexdigest = hashlib.md5(path).hexdigest()

        # Create the lock path based on the given path
        super(TemporaryLock, self).__init__(os.path.join(self.DIRECTORY, hexdigest), timeout)
