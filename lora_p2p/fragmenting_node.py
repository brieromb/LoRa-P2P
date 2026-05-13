from .reliable_communicating_node import ReliableCommunicatingNode
from .receiving.received_message import ConnectionQualityMeasurements
from .lora_node import LoRaNode
from .fragment import Fragment, BigMessage

import random
import threading

class FragmentingNode:
    def __init__(
            self,
            lora_node: LoRaNode,
            incoming_message_handler = lambda x: x,
    ):
        """Constructs a FragmentingNode.
        Args:
                lora_node: An instantiated LoRaNode
                incoming_message_handler: custom handler that handles complete incoming message tuples.
                    message tuples are (bytes, list[ConnectionQualityMeasurements])"""

        # Use an underlying ReliableCommunicatingNode for sending Fragments.
        self.reliable_communicating_node = ReliableCommunicatingNode(
            lora_node,
            self._handle_received
        )
        self.incomplete_messages: dict[int, BigMessage] = dict() # BigMessage id -> incomplete BigMessage
        self.incoming_message_handler = incoming_message_handler
    
    def send_message(self, large_data: bytes, max_retries_packet:int, retransmission_timeout_packet:float):
        # New id for the message.
        id_ = self._generate_message_id()
        big_message = BigMessage.from_bytes(id_, large_data)
        fragments: list[Fragment] = big_message.get_fragments()

        #print(f"FragNode {id(self)}: Sending {len(fragments)} packets for message {large_data}")

        # Send all fragments one by one for now. For simplicity.
        for (i, fragment) in enumerate(fragments):
            frag_bytes = fragment.serialize()
            try:
                # TODO find good retransmission parameters
                response_tuple = self.reliable_communicating_node.send_reliably(
                    frag_bytes,
                    max_retries=max_retries_packet,
                    retransmission_timeout=retransmission_timeout_packet
                )
                """
                response_data = response_tuple[0]
                # Check if the response is as expected an ACK for the sent message.
                expected_ack: bytes = fragment.get_expected_ack_message()
                if response_data != expected_ack:
                    raise RuntimeError(f"Expected an ACK for the sent fragment ({expected_ack}). Instead got: {response_data}")
                print(f"RECEIVED ACK FOR FRAGMENT {fragment.data}")
                """
            except TimeoutError:
                raise TimeoutError(f"Time out in waiting for ACK for packet {i} out of {len(fragments)}, in sending a large message of {len(large_data)} bytes.")
        # The message was completely sent and received on the other side.

    def _handle_received(self, message_tuple: tuple[bytes,ConnectionQualityMeasurements]) -> bytes:
        """Handles receiving messages. This function is the underlying ReliableCommunicatingNode's `incoming_message_handler`.
        It handles received Fragments of BigMessages"""

        message_data: bytes = message_tuple[0]
        try:
            fragment: Fragment = Fragment.from_bytes(message_data)
            matching_message: BigMessage
            # Find the matching incomplete message for this fragment (or create a new one if no match)
            if fragment.message_id in self.incomplete_messages:
                # earlier fragment for this message was received.
                matching_message = self.incomplete_messages[fragment.message_id]
                matching_message.add_fragment(fragment, message_tuple[1])
            else:
                # This is the first fragment received for this message. This fragment starts a new message reconstruction.
                matching_message: BigMessage = BigMessage([fragment], message_tuple[1])
                self.incomplete_messages[matching_message.id] = matching_message

            if matching_message.is_complete():
                #print(f"FragNode {id(self)}: message complete with payload: {matching_message.get_payload_tuple()}")
                # Remove the message from the incompleted messages.
                self.incomplete_messages.pop(matching_message.id)
                # Return the completed message to the callback.
                message_handler_thread = threading.Thread( # DOING THIS IN A THREAD FIXES OTHERWISE REPLIES BEING SENT BEFORE ACKS.
                    target=self.incoming_message_handler,
                    args=(matching_message.get_payload_tuple(),)
                )
                message_handler_thread.start()
            #print(f"FragNode {id(self)}: sending ACK for fragment #{fragment.sequence_number}: ({fragment.data})")
            # Return ACK for receiving the fragment.
            return fragment.get_expected_ack_message()
            
        except ValueError:
            print(f"⚠️ WARNING: FragmentingNode received a message that couldn't be interpreted as a Fragment: {message_data}. Dropping message.")
            
    
    def _generate_message_id(self) -> int:
        """Generates a random message id for a message to be sent."""
        return random.randint(0, BigMessage.MAX_ID)
