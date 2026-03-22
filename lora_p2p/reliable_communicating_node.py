import threading
import time
from queue import Queue

from .lora_node import LoRaNode
from .receiving.received_message_data_parser import ReceivedMessage
from .receiving.response import Response
from .transmission import Transmission, TransmissionState

class ReliableCommunicatingNode:
    """
    A reliable communicating node for sending messages over LoRa.
    Uses acknowledgements and retransmissions to ensure message delivery."""

    def __init__(
            self,
            lora_node: LoRaNode,
            incoming_message_handler = lambda _: b"OK!" # Accepts an incoming ReceivedMessage, and returns OK! as an answer
    ):
        """incoming messages to a callback that handles ReceivedMessages.
        
        Args:
            lora_node: An instantiated LoRaNode that this class uses to communicate. This is just a layer above the lora node.
            max_retries: The maximum number of times that a message is resend when no ACK is retured.
            incoming_message_handler: A callback that accepts instances of ReceivedMessage, and returns a reply to be sent back. This callback is called whenever a message arrives."""

        self.lora_node = lora_node
        self.incoming_message_handler = incoming_message_handler

        self.lora_node.set_on_received_callback(self._on_receive)
        
        self.send_queue : Queue = Queue() # Queue of transmissions to be sent reliably

        self.current_transmission : Transmission = None # The transmission that is currently being sent/waiting for ACK

    def send_reliably(self, data: bytes, max_retries: int = 3, retransmission_timeout: float = 5.0):
        """Sends a message using best effort, but non-blocking.
        If no response is sent within the retransmission timeout,
        it will retry until the number of max retries is reached."""

        # Create new transmission object and add it to the send queue
        transmission = Transmission(data, max_retries, retransmission_timeout)
        self.send_queue.put(transmission)

        # If there is no current transmission being sent, start handling the next one in the queue
        if self.current_transmission is None:
            self._handle_next_in_send_queue()
        else:
            print("Currently busy sending another message, adding to send queue")
    
    def send_reliably_wait_for_answer(self, data: bytes, max_retries: int = 3, retransmission_timeout: float = 5.0) -> bytes:
        """Sends a message using best effort and blocks until a response is received or the max retries are reached.
        If the max retries are reached without any response, a TimeoutException is raised."""

        # Create new transmission object and add it to the send queue
        transmission = Transmission(data, max_retries, retransmission_timeout)
        self.send_queue.put(transmission)

        # If there is no current transmission being sent, start handling the next one in the queue
        if self.current_transmission is None:
            self._handle_next_in_send_queue()
        else:
            print("Currently busy sending another message, adding to send queue")
        
        transmission.terminated.wait(timeout=None) # Wait until the transmission is finished successfully or unsuccessfully.

        if transmission.state == TransmissionState.FAILED:
            # First clear the transmission and send the next message in queue before throwing an error.
            # Else the queue would become blocked.
            self.current_transmission = None
            self._handle_next_in_send_queue()
            raise TimeoutError("Connection timed out: The number of max retransmissions was reached, without receiving a reply.")
        else: # The transmission was successful. Return the reply
            return transmission.get_response()
    
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

    def _on_receive(self, message: ReceivedMessage):
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
                    self.current_transmission.mark_acknowledged(payload_as_response.get_contents())
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


def testReliableCommunicatingNode():
    # Some end-to-end tests for ReliableCommunicatingNode
    
    node1 = LoRaNode(port="COM4")
    reliable_node1 = ReliableCommunicatingNode(node1)

    # The receiving node is not yet initialized, so this should time out.
    try:
        reliable_node1.send_reliably_wait_for_answer(b"Should not arrive", 1, 0.5)
        assert False, "No error was thrown, but the message couldn't have arrived."
    except TimeoutError:
        print("Success: the message that couldn't arrive, did not arrive.")

    # Initialize a second node and do some more tests.
    node2 = LoRaNode(port="COM5")
    reliable_node2 = ReliableCommunicatingNode(node2)

    answer = reliable_node2.send_reliably_wait_for_answer(b"LOL", 1, 0.5)
    print(f"WAITED FOR AND GOT {answer}")

    reliable_node1.send_reliably(b"HELLO WORLD")
    print("DID SOME WORK WHILE WAITING")
    time.sleep(2)