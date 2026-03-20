from enum import Enum
import threading
from lora_node import LoRaNode
from queue import Queue
from received_message_data_parser import ReceivedMessage
from response import Response

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

    def __init__(
            self,
            lora_node: LoRaNode,
            max_retries=3,
            incoming_message_handler = lambda _: b"OK!" # Accepts an incoming ReceivedMessage, and returns OK! as an answer
    ):
        """incoming messages to a callback that handles ReceivedMessages.
        
        Args:
            lora_node: An instantiated LoRaNode that this class uses to communicate. This is just a layer above the lora node.
            max_retries: The maximum number of times that a message is resend when no ACK is retured.
            incoming_message_handler: A callback that accepts instances of ReceivedMessage, and returns a reply to be sent back. This callback is called whenever a message arrives."""

        self.lora_node = lora_node
        self.max_retries = max_retries
        self.incoming_message_handler = incoming_message_handler

        self.lora_node.set_on_received_callback(self.on_receive)
        
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
            # Check if the received message is a response to an earlier sent message.
            payload_as_response = Response.from_bytes(payload)
            if payload_as_response is not None:
                # The payload could be interpreted as a response.
                # Check if the response is for the last sent message.
                if payload_as_response.is_response_for(self.current_transmission.send_data):
                    print(f"Received: {str(payload_as_response)}")
                    self.current_transmission.mark_acknowledged()
                    self.current_transmission = None # Clear the current transmission before handling the next one in the queue
                    self._handle_next_in_send_queue()
                else:
                    print(f"⚠️ WARNING: received response to an unknown message: {payload_as_response.get_original_message()}. Expected a response for {self.current_transmission.send_data}")
            else:
                # The received message is not a response to a message that this node sent.
                # Send an acknowledgement back to the sender for the received message
                answer: bytes = self.incoming_message_handler(message)
                # Send a response back to the sender
                resp = Response(response_for=message, response_contents=answer)
                # Just send, without expecting a reply to this reply
                self.lora_node.send(resp.as_bytes())
        else:
            print(f"⚠️ WARNING: received message without payload: {message}")
