from lora_p2p.receiving.received_message import ConnectionQualityMeasurements

from .fragmenting_node import FragmentingNode
from .lora_node import LoRaNode

import threading
import random

class MainNode:
    """A highest level node that sends messages and can identify received messages as responses to earlier sent messages."""
    RESPONSE_IDENTIFIER = b"F"
    REQUEST_IDENTIFIER = b"0"
    MESSAGE_ID_SIZE_BYTES = 3 # Allows for 8**3 = 512 unique messages in transit at the same time.

    PREAMBLE_LENGTH = len(RESPONSE_IDENTIFIER)
    HEADER_LENGTH = PREAMBLE_LENGTH + MESSAGE_ID_SIZE_BYTES

    def __init__(self,
                 lora_node: LoRaNode,
                 incoming_message_handler=lambda x: b'Whatever dude.',
                 max_retries_packet:int = 2,
                 retransmission_timeout_packet:float = 2.0
                ):
        """Initializes a MainNode.
        
        Args:
            lora_node: an instance of a real or mock LoRaNode.
            incoming_message_handler: A message handler that receives incoming messages `tuple(bytes, ConnectionQualityMeasurements)` and returns a response to them.
            max_retries_packet:
            retransmission_timeout_packet"""

        assert len(self.REQUEST_IDENTIFIER) == len(self.RESPONSE_IDENTIFIER), "Request- and response identifiers should be of the same length."

        self.fragmenting_node: FragmentingNode = FragmentingNode(lora_node, self._handle_random_incoming_message)
        self.incoming_message_handler = incoming_message_handler
        self.max_retries_packet = max_retries_packet
        self.retransmission_timeout_packet = retransmission_timeout_packet

        self.waiting_messages : dict[bytes, threading.Event] = dict() # Receive events for all waiting messages.
        self.unhandled_responses : dict[bytes, tuple[bytes, ConnectionQualityMeasurements]] = dict() # Unhandled responses for messages.
        self.lock = threading.Lock() # Lock for the dict objects.
    
    def send_and_wait(self, payload: bytes) -> tuple[bytes, ConnectionQualityMeasurements]:
        """Sends some message in bytes. Waits for and returns the response.
        If one of the packets could not arrive, a TimeourError is thrown."""
        with self.lock:
            # Add the message to the send queue
            id: bytes = self._create_message_id()
            # Make receive event to wait for
            receive_event = threading.Event()
            self.waiting_messages[id] = receive_event

        # construct complete message and send.
        complete_message = self.REQUEST_IDENTIFIER + id + payload
        self.fragmenting_node.send_message(complete_message, self.max_retries_packet, self.retransmission_timeout_packet)

        if receive_event.wait(): # No timeout. The packets themselves will throw TimeoutErrors
            # Succesfully received the message.
            # Remove this message's data from the dicts and return response.
            with self.lock:
                #print("MainNode: Response received. Terminating send.")
                self.waiting_messages.pop(id)
                response = self.unhandled_responses.pop(id)
            return response
        else:
            raise TimeoutError("Timer ran out before receiving the response.")

    
    def _handle_random_incoming_message(self, message_tuple: tuple[bytes, ConnectionQualityMeasurements]) -> None:
        """Callback that handles all incoming messages.
        It handles both new messages and responses to earlier sent messages.
        This method can distinguish the two cases and act accordingly."""
        payload = message_tuple[0]

        if len(payload) < self.PREAMBLE_LENGTH + self.MESSAGE_ID_SIZE_BYTES:
            print("⚠️ WARNING: A message was received that was too short to contain the necessary header information. Dropping message.")
            return
        preamble = payload[0:self.PREAMBLE_LENGTH]
        id = payload[self.PREAMBLE_LENGTH:self.PREAMBLE_LENGTH + self.MESSAGE_ID_SIZE_BYTES]

        if preamble == self.REQUEST_IDENTIFIER:
            # Handle new message. Formulate a response.
            response = self.incoming_message_handler((payload[self.HEADER_LENGTH:], message_tuple[1]))
            # Add header and send the response
            full_response = self.RESPONSE_IDENTIFIER + id + response
            self.fragmenting_node.send_message(full_response, self.max_retries_packet, self.retransmission_timeout_packet)
        elif preamble == self.RESPONSE_IDENTIFIER:
            # Handle response to earlier message.
            # Find the earlier message.
            try:
                with self.lock:
                    receive_event: threading.Event = self.waiting_messages[id]
                    self.unhandled_responses[id] = (payload[self.HEADER_LENGTH:], message_tuple[1])
                    receive_event.set()
            except KeyError:
                print("⚠️ WARNING: Received a response to a message that was either not sent or has already received a response. Dropping message.")
                return
            
        else:
            print("⚠️ WARNING: A message was received that didn't have the correct preamble to be either a response or request. Dropping message.")
            return
    
    def _create_message_id(self) -> bytes:
        """Creates a unique message id"""
        id: bytes = random.randbytes(self.MESSAGE_ID_SIZE_BYTES)
        # Reroll if message ID is already in use.
        if id not in self.waiting_messages:
            return id
        else:
            return self._create_message_id()

