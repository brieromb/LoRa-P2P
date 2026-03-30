import threading

class SingleExecutionGuard:
    """A decorator class that ensures that only a single execution of the decorated function can be running at the same time.
    This is used to prevent multiple threads from sending AT commands at the same time, that end up mixing their responses
    
    Currently this has the side effect of multiple threads for different LoRaKitController instances blocking each other,
    but this is not a problem since mostly there is only one LoRaKitController instance."""

    def __init__(self, func):
        self.func = func
        self._lock = threading.Lock()

    def __call__(self, *args, **kwargs):
        # Only one thread can pass this point at a time
        with self._lock:
            return self.func(*args, **kwargs)
