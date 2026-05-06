import threading
from enum import Enum
import random
import time

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
        self.max_retries = 16
        self.timeout = timeout

        self.state = TransmissionState.UNACKNOWLEDGED
        self.response = None

        self.retries = 0
        self.terminated = threading.Event() # Event that signals that the transmission is finished. Either response received or reached max retries.

        self.last_timer_start_time = time.time() # Keep last timeout start time to detect possible collisions.

    def mark_acknowledged(self, response):
        """Mark the current transmission as acknowledged,
        by providing the ReceivedResponse instance that replies to the sent data."""

        self.state = TransmissionState.ACKNOWLEDGED
        self.response = response
        self.terminated.set()
    
    def get_response(self):
        assert self.response is not None, "tried to access a response to a transmission that hasn't arrived (yet)"
        return self.response
    
    def get_send_data(self) -> bytes:
        return self.send_data

    def _mark_unsuccessful(self):
        self.state = TransmissionState.FAILED
        self.terminated.set()
    
    def retransmission_timer(self, last_received_time, retransmit_callback):
        """
        Starts a timer to wait for an acknowledgement. If the timer expires before an ACK is received, it will trigger a retransmission if the max retries has not been reached."""        

        if (self.last_timer_start_time < last_received_time):
            # Possible collision detected! (last timer start was before last received)
            print("(POSSIBLE COLLISION DETECTED)")
        else:
            # Mark unsuccessful if no collision detected and a certain timeout has been reached.
            if self.last_timer_start_time < time.time() - 10:
                self._mark_unsuccessful()
                return

        # Wait until ACK received or timeout
        # Calculate the expected waiting time based on exponential backoff.
        slot_time = 1.75
        k = min(self.retries + 1, 4)
        wait_time = random.randint(1, pow(2,k)) * slot_time
        #print(f"Timer #{self.retries} of {wait_time} seconds started")
        if self.terminated.wait(wait_time):
            #print(f"ACK received on attempt #{self.retries} -> cancel retransmission")
            return

        # Timeout occurred. mark as failed if we have reached the max retries.
        self.retries += 1
        if (self.retries > self.max_retries):
            print("Max retries reached -> marking transmission as failed")
            self._mark_unsuccessful()
        else:
            print(f"RETRANSMITTING due to timeout after {wait_time}s on attempt #{self.retries}")
            retransmit_callback()
    
    def is_finished(self) -> bool:
        return self.terminated.is_set()