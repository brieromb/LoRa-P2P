"""Code from the official pyserial docs: https://www.pyserial.org/docs/reading-data"""

import threading
import queue
import time

class ThreadedSerialReader:
    def __init__(self, ser, queue_size=1000):
        self.ser = ser
        self.data_queue = queue.Queue(maxsize=queue_size)
        self.running = True
        self.thread = None

        # OWN ADDITION:
        # Optional: You can set a custom function to redirect incoming data instead of the queue, for example to process it directly in the callback instead of having to poll the queue.
        self.data_redirect_function = None
        self.redirect = False

    def start(self):
        """Start background reading thread"""
        self.thread = threading.Thread(target=self._read_loop)
        self.thread.daemon = True
        self.thread.start()
    
    def set_redirect_data_callback(self, redirect_function):
        """OWN ADDITION: Set a function to redirect incoming data to instead of the queue"""
        self.data_redirect_function = redirect_function
    
    def toggle_redirect_data(self, enable: bool):
        """OWN ADDITION: Toggle redirecting incoming data to the redirect function instead of the queue"""
        if not enable:
            self.redirect = False
        else:
            if not self.data_redirect_function:
                print("No redirect function set, cannot enable redirect")
                return
            self.redirect = True
            # If there is still data in the queue, redirect all of it to the redirect function
            data = self.get_data()
            while data is not None:
                self.data_redirect_function(data)
                data = self.get_data()

    def is_redirecting(self) -> bool:
        """OWN ADDITION: Check if the serial reader is redirecting or putting in queue"""
        return self.data_redirect_function is not None and self.redirect

    def _read_loop(self):
        """Background reading loop"""
        while self.running:
            try:
                if self.ser.in_waiting:
                    data = self.ser.read(self.ser.in_waiting)
                    if data:
                        try:
                            if self.redirect:
                                self.data_redirect_function(data)
                            else:
                                self.data_queue.put(data, timeout=0.1)
                        except queue.Full:
                            print("⚠️  Queue full, dropping data")
                else:
                    time.sleep(0.001)  # Small delay when no data
            except Exception as e:
                if self.running:
                    print(f"Read thread error: {e}")
    
    def get_data(self, timeout=0.1):
        """Get data from queue"""
        try:
            return self.data_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def get_all_data(self):
        """Get all queued data"""
        data = []
        while not self.data_queue.empty():
            try:
                data.append(self.data_queue.get_nowait())
            except queue.Empty:
                break
        return b''.join(data)
    
    def stop(self):
        """Stop reading thread"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)

""" Example usage
# Usage
reader = ThreadedSerialReader(ser)
reader.start()

try:
    while True:
        data = reader.get_data(timeout=1)
        if data:
            print(f"Got {len(data)} bytes")
        else:
            print("No data received")
        time.sleep(0.1)
finally:
    reader.stop()
"""