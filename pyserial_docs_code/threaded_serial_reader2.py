import threading
import queue
import time

class ThreadedSerialReader:
    """ee https://www.pyserial.org/docs/reading-data"""
    def __init__(self, ser, queue_size=1000):
        self.ser = ser
        self.data_queue = queue.Queue(maxsize=queue_size)
        self.running = True
        self.thread = None
        self.blocked = threading.Event() # Own addition to allow for pausing of the ThreadedSerialReader.

    def pause(self):
        self.blocked.set()
    
    def resume(self):
        self.blocked.clear()
    
    def is_paused(self):
        return self.blocked.is_set()
    
    def start(self):
        """Start background reading thread"""
        self.thread = threading.Thread(target=self._read_loop)
        self.thread.daemon = True
        self.thread.start()
    
    def _read_loop(self):
        """Background reading loop"""
        while self.running:
            try:
                if not self.blocked.is_set() and self.ser.in_waiting:
                    data = self.ser.read(self.ser.in_waiting)
                    if data:
                        try:
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
            self.thread.join(timeout=None)
    
    def __del__(self):
        """Stop the running thread when the object gets deleted"""
        self.stop()

"""
if __name__ == '__main__':
    # EXAMPLE USAGE
    ser = serial.Serial(port="COM5", baudrate=9600, timeout=1)
    reader = ThreadedSerialReader(ser)
    reader.start()

    reader.pause()
    print(write_with_confirm(ser, b'AT\r\n', b'+AT: OK'))
    print(write_with_confirm(ser, b'AT+MODE=TEST\r\n', b'+MODE: TEST'))
    print(write_with_confirm(ser, b'AT+TEST=RXLRPKT\r\n', b'+TEST: RXLRPKT'))
    reader.resume()

    try:
        while True:
            data = reader.get_data(timeout=1)
            if data:
                print(f"Got {len(data)} bytes: {data}")
            else:
                print("No data received")
            time.sleep(0.1)
    finally:
        reader.stop()
"""