import os
import time
import random
import hashlib
import tempfile
import threading

from fsdicts.encoders import ENCODING


class FileLock(object):

    def __init__(self, path):
        # Create the lock path
        self._path = path + ".lock"

        # Create internal state
        self._locked = False

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

        # Try removing the directory
        os.rmdir(self._path)

        # Update the lock status
        self._locked = False

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


class LocalLock(FileLock):

    def __init__(self, path, temporary_directory=os.path.join(tempfile.gettempdir(), __name__)):
        # Create the directory if it does not exist
        if not os.path.isdir(temporary_directory):
            os.makedirs(temporary_directory)

        # If the path is a string, encode it
        if isinstance(path, str):
            path = path.encode(ENCODING)

        # Create hexdigest from path
        hexdigest = hashlib.md5(path).hexdigest()

        # Create the lock path based on the given path
        super(LocalLock, self).__init__(os.path.join(temporary_directory, hexdigest))


class ReferenceLock(object):

    def __init__(self, lock):
        # Initialize the internal lock
        self._lock = lock

        # Initialize the counter
        self._thread = None
        self._references = 0

    def acquire(self, blocking=True, timeout=None):
        # Fetch the current thread
        current_thread = threading.current_thread()

        # If there are no references, lock the lock
        if current_thread != self._thread:
            # Lock the lock
            self._lock.acquire(blocking=blocking, timeout=timeout)

            # Set the thread
            self._thread = current_thread

        # Increment the reference count
        self._references += 1

    def release(self):
        # Fetch the current thread
        current_thread = threading.current_thread()

        # Make sure the thread is the locking thread
        if current_thread != self._thread:
            raise RuntimeError("Thread %r can't release %r" % (current_thread, self))

        # Check the reference count
        if not self._references:
            raise RuntimeError("Already released")

        # Decrement the references
        self._references -= 1

        # Check if should release lock
        if not self._references:
            # Clear the thread
            self._thread = None

            # Release the lock
            self._lock.release()

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
        return "<%s, %d references>" % (self.__class__.__name__, self._references)
