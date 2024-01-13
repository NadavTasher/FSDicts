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

    def _try_acquire(self):
        try:
            # Try creating the directory
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
