import threading
from enum import Enum

class TransmissionState(Enum):
    UNACKNOWLEDGED = 1
    ACKNOWLEDGED = 2
    FAILED = 3

class Transmission():
    """
    Represents a message transmission with its state and retry information.
    Has a threading event `terminated` which will be signaled when the transmission was successful or reached max retries.
    """

    def __init__(self, send_data: bytes, max_retries: int, timeout: float):
        assert isinstance(send_data, bytes), "the data to be sent should be bytes"
        assert isinstance(max_retries, int) and max_retries >= 0, "max retries should be an integer >= 0"
        assert isinstance(timeout, float) and timeout > 0, "retransmission timeout should be a float > 0"

        self.send_data = send_data
        self.max_retries = max_retries
        self.timeout = timeout

        self.state = TransmissionState.UNACKNOWLEDGED
        self.response_payload = None

        self.retries = 0
        self.terminated = threading.Event() # Event that signals that the transmission is finished. Either response received or reached max retries.

    def mark_acknowledged(self, response_payload: bytes):
        self.state = TransmissionState.ACKNOWLEDGED
        self.response_payload = response_payload
        self.terminated.set()
    
    def get_response(self):
        assert self.response_payload is not None, "tried to access a response to a transmission that hasn't arrived (yet)"
        return self.response_payload

    def _mark_unsuccessful(self):
        self.state = TransmissionState.FAILED
        self.terminated.set()
    
    def retransmission_timer(self, retransmit_callback):
        """
        Starts a timer to wait for an acknowledgement. If the timer expires before an ACK is received, it will trigger a retransmission if the max retries has not been reached."""        
        
        print("Timer started")

        # Wait until ACK received or timeout
        if self.terminated.wait(self.timeout):
            print("ACK received -> cancel retransmission")
            return

        # Timeout occurred. mark as failed if we have reached the max retries.
        self.retries += 1
        if (self.retries > self.max_retries):
            print("Max retries reached -> marking transmission as failed")
            self._mark_unsuccessful()
        else:
            print("Timeout -> retransmitting")
            retransmit_callback()