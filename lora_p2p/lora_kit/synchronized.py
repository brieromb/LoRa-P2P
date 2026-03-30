import threading
from functools import wraps

def synchronized(method):
    """A wrapper function that ensures that only a single execution of the wrapped function can be running at the same time.
    This is used to prevent multiple threads from sending AT commands at the same time to the same hardware.
    Otherwise, the responses from the hardware can get mixed up and cause errors.
    When used by multiple instances of the same class,
    it still allows for the different instances to execute the method at the same time,
    as the lock is per instance."""

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        if not hasattr(self, "_instance_lock"):
            self._instance_lock = threading.Lock()

        with self._instance_lock:
            return method(self, *args, **kwargs)

    return wrapper
