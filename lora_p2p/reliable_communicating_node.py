import threading
from queue import Queue

from .receiving.received_message import ConnectionQualityMeasurements
from .receiving.received_response import ReceivedResponse

from .lora_node import LoRaNode
from .receiving.received_message_data_parser import ReceivedMessage
from .receiving.response import ResponsePayload
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
            incoming_message_handler: A callback that handles a tuple like (received_message (bytes), ConnectionQualityMeasurements), and formulates a reply (in bytes) to be sent back. This callback is called whenever a message arrives."""

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
    
    def send_reliably_wait_for_answer(self, data: bytes, max_retries: int = 2, retransmission_timeout: float = 2.0) -> tuple[bytes, ConnectionQualityMeasurements]:
        """Sends a message using best effort and blocks until a response is received or the max retries are reached.
        The response that is returned is a tuple containing the response bytes and the connection quality measurements.
        If the max retries are reached without getting any response, a TimeoutException is raised."""

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
            return transmission.get_response().as_tuple()
    
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
        """Processes received messages.
        Checks if they are responses to a previously sent message or if they are new messages.
        In the latter case the function will respond back using the incoming_message_handler.
        Also prints appropriate warnings when unexpected cases occur."""

        # Process the received message and send an acknowledgement back to the sender
        if message.has_payload():
            try: # Try to interpret the received message as a received response.
                response = ReceivedResponse(message)
                if response.finishes_transmission(self.current_transmission):
                    self.current_transmission.mark_acknowledged(response)
                    self.current_transmission = None # Clear the current transmission before handling the next one in the queue
                    self._handle_next_in_send_queue()
                else:
                    print(f"⚠️ WARNING: received response to an unknown message with digest: {response.get_original_message_digest()}. Expected a response for {self.current_transmission.get_send_data()}")

            except ValueError: # The message could not be interpreted as a response.
                # So it must be an original new message that needs a response from this node.
                answer: bytes = self.incoming_message_handler(message.as_tuple())
                # Send a response back to the sender
                resp = ResponsePayload(response_for=message, response_contents=answer)
                # Just send, without expecting a reply to this reply
                self.lora_node.send(resp.as_bytes())
        else: 
            print(f"⚠️ WARNING: received message without payload: {message}")
