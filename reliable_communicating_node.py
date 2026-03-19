from enum import Enum
import threading
from lora_node import LoRaNode
from queue import Queue
from serial_line_processor import ReceivedMessage

class TransmissionState(Enum):
    UNACKNOWLEDGED = 1
    ACKNOWLEDGED = 2
    FAILED = 3

class Transmission():
    """
    Represents a message transmission with its state and retry information."""

    def __init__(self, send_data: bytes, max_retries: int, timeout: float):
        assert(isinstance(send_data, bytes))
        self.send_data = send_data
        self.max_retries = max_retries
        self.timeout = timeout
        self.state = TransmissionState.UNACKNOWLEDGED

        self.retries = 0
        self.acknowledged = threading.Event() # Event to signal that an ACK has been received for this transmission

    def mark_acknowledged(self):
        self.acknowledged.set()
        self.state = TransmissionState.ACKNOWLEDGED
    
    def retransmission_timer(self, retransmit_callback):
        """
        Starts a timer to wait for an acknowledgement. If the timer expires before an ACK is received, it will trigger a retransmission if the max retries has not been reached."""        
        
        print("Timer started")

        # Wait until ACK received or timeout
        if self.acknowledged.wait(self.timeout):
            print("ACK received -> cancel retransmission")
            return

        # Timeout occurred. mark as failed if we have reached the max retries.
        self.retries += 1
        if (self.retries > self.max_retries):
            print("Max retries reached -> marking transmission as failed")
            self.state = TransmissionState.FAILED
        else:
            print("Timeout -> retransmitting")
            retransmit_callback()

class ReliableCommunicatingNode:
    """
    A reliable communicating node for sending messages over LoRa.
    Uses acknowledgements and retransmissions to ensure message delivery."""

    def __init__(self, lora_node: LoRaNode, max_retries=3):
        self.lora_node = lora_node
        self.lora_node.set_on_received_callback(self.on_receive)

        self.max_retries = max_retries
        self.send_queue : Queue = Queue() # Queue of transmissions to be sent reliably

        self.retransmission_timeout = 5 # Time to wait for an acknowledgement before retransmitting

        self.current_transmission : Transmission = None # The transmission that is currently being sent/waiting for ACK

    def send_reliably(self, data):
        # Create new transmission object and add it to the send queue
        transmission = Transmission(data, self.max_retries, self.retransmission_timeout)
        self.send_queue.put(transmission)

        # If there is no current transmission being sent, start handling the next one in the queue
        if self.current_transmission is None:
            self._handle_next_in_send_queue()
        else:
            print("Currently busy sending another message, adding to send queue")
    
    def _handle_next_in_send_queue(self):
        if not self.send_queue.empty():
            next_transmission = self.send_queue.get()
            self.current_transmission = next_transmission
            self._transmit_current()
    
    def _transmit_current(self):
        transmission = self.current_transmission
        self.lora_node.send(transmission.send_data)
        # Start the retransmission timer in a separate thread so that we can wait for the ACK without blocking the main thread.
        # If the timer expires before an ACK is received, it will trigger a retransmission if the max retries has not been reached.
        timer_thread = threading.Thread(
            target=transmission.retransmission_timer,
            args=(self._transmit_current,))
        timer_thread.start()

    def on_receive(self, message: ReceivedMessage):
        # Process the received message and send an acknowledgement back to the sender
        if message.has_payload():
            payload = message.get_payload()
            if payload.startswith(b"ACK:"):
                # Handle the acknowledgement for a sent message
                acked_message = payload[len(b"ACK:"):]
                if self.current_transmission and self.current_transmission.send_data == acked_message:
                    print(f"Acknowledgement received for message: {acked_message}")
                    self.current_transmission.mark_acknowledged()
                    self.current_transmission = None # Clear the current transmission before handling the next one in the queue
                    self._handle_next_in_send_queue()
                else:
                    print(f"Received ACK for unknown message: {acked_message}. Expected an ACK for {self.current_transmission.send_data}")
            else:
                # Send an acknowledgement back to the sender for the received message
                print(f"Received message: {payload}")
                # Send an acknowledgement back to the sender
                ack_message = b"ACK:" + payload
                self.lora_node.send(ack_message)
        else:
            print(f"Warning: Received message without payload: {message}")
