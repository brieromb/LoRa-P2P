from .reliable_communicating_node import ReliableCommunicatingNode
from .receiving.received_message import ConnectionQualityMeasurements
from .lora_node import LoRaNode

import random

class Fragment:
    """A serialized fragment of a message, with fields:
    | msg_id | total_frags | seq_num | payload_len | data |
    """
    MESSAGE_ID_BYTES = 4
    TOTAL_FRAGS_BYTES = 2
    SEQ_NUM_BYTES = 2
    PAYLOAD_LEN_BYTES = 2 # TODO maybe remove

    TOTAL_HEADER_LEN = MESSAGE_ID_BYTES + TOTAL_FRAGS_BYTES + SEQ_NUM_BYTES + PAYLOAD_LEN_BYTES
    MAX_PAYLOAD_SIZE = 50 # TODO derive this from hardware limit.

    def __init__(self, message_id: int, total_fragments: int, sequence_number: int, data: bytes):
        self.data = data
        self.message_id = message_id
        self.total_fragments = total_fragments
        self.sequence_number = sequence_number
        self.payload_length = len(data)
    
    def get_expected_ack_message(self) -> bytes:
        """ACK message for the fragment, containing the message id and sequence number."""
        return b'ACK' + self.message_id.to_bytes(self.MESSAGE_ID_BYTES, byteorder='big') + self.sequence_number.to_bytes(self.SEQ_NUM_BYTES, byteorder='big')
    
    def serialize(self) -> bytes:
        """Serializes the fragment into bytes, so that it can be sent over the LoRa."""
        return (
            self.message_id.to_bytes(self.MESSAGE_ID_BYTES, byteorder='big') +
            self.total_fragments.to_bytes(self.TOTAL_FRAGS_BYTES, byteorder='big') +
            self.sequence_number.to_bytes(self.SEQ_NUM_BYTES, byteorder='big') +
            self.payload_length.to_bytes(self.PAYLOAD_LEN_BYTES, byteorder='big') +
            self.data
        )
    
    @staticmethod
    def from_bytes(bytes_data: bytes):
        """Deserializes a fragment from bytes."""
        if len(bytes_data) < Fragment.TOTAL_HEADER_LEN:
            return ValueError(f"Cannot convert byte sequence to Fragment. byte sequence length ({len(bytes_data)}) is smaller than Fragment header length({Fragment.TOTAL_HEADER_LEN}).")

        message_id = int.from_bytes(bytes_data[0:Fragment.MESSAGE_ID_BYTES], byteorder='big')
        total_fragments = int.from_bytes(bytes_data[Fragment.MESSAGE_ID_BYTES:Fragment.MESSAGE_ID_BYTES + Fragment.TOTAL_FRAGS_BYTES], byteorder='big')
        sequence_number = int.from_bytes(bytes_data[Fragment.MESSAGE_ID_BYTES + Fragment.TOTAL_FRAGS_BYTES:Fragment.MESSAGE_ID_BYTES + Fragment.TOTAL_FRAGS_BYTES + Fragment.SEQ_NUM_BYTES], byteorder='big')
        payload_length = int.from_bytes(bytes_data[Fragment.MESSAGE_ID_BYTES + Fragment.TOTAL_FRAGS_BYTES + Fragment.SEQ_NUM_BYTES:Fragment.MESSAGE_ID_BYTES + Fragment.TOTAL_FRAGS_BYTES + Fragment.SEQ_NUM_BYTES + Fragment.PAYLOAD_LEN_BYTES], byteorder='big')
        data = bytes_data[Fragment.MESSAGE_ID_BYTES + Fragment.TOTAL_FRAGS_BYTES + Fragment.SEQ_NUM_BYTES + Fragment.PAYLOAD_LEN_BYTES:Fragment.MESSAGE_ID_BYTES + Fragment.TOTAL_FRAGS_BYTES + Fragment.SEQ_NUM_BYTES + Fragment.PAYLOAD_LEN_BYTES + payload_length]
        return Fragment(message_id, total_fragments, sequence_number, data)


class BigMessage:
    """A message that is too big to be sent in one fragment, and is therefore split into multiple fragments.
    
    Params:
        id: the unique identifier of the message. used to link fragments to it.
        fragments: the fragments for this message. This can be incomplete for messages that are getting reconstructed.
        total_fragments: number of fragments that this message consists of.

    """

    MAX_AMOUNT_FRAGMENTS = 8**Fragment.TOTAL_FRAGS_BYTES - 1 # Max representable id in the fragment header.
    MAX_ID = 8**Fragment.MESSAGE_ID_BYTES - 1

    def __init__(self, fragments: list[Fragment]):
        """Construct an incomplete BigMessage using Fragments.
        This constructor assumes all fragments have the same message id and no duplicates are in the list."""

        assert len(fragments) > 0, "Need at least one fragment to start constructing a BigMessage."
        self.fragments = fragments
        self.total_fragments = fragments[0].total_fragments
        self.id = fragments[0].message_id

    @classmethod
    def from_bytes(cls, id: int, data: bytes):
        """Construct a new BigMessage by splitting the given data into fragments, and assigning them a message id and sequence numbers."""

        fragments: list[Fragment] = []
        total_fragments = len(data) // Fragment.MAX_PAYLOAD_SIZE + (1 if len(data) % Fragment.MAX_PAYLOAD_SIZE > 0 else 0)
        if total_fragments > cls.MAX_AMOUNT_FRAGMENTS:
            raise RuntimeError(f"The message could not be fragmented. Otherwise too many fragments ({total_fragments}). The Fragment header only supports up to {cls.MAX_AMOUNT_FRAGMENTS} fragments per message.")
        for i in range(0, len(data), Fragment.MAX_PAYLOAD_SIZE):
            fragment_data = data[i:i + Fragment.MAX_PAYLOAD_SIZE]
            fragment = Fragment(
                id,
                total_fragments,
                i // Fragment.MAX_PAYLOAD_SIZE,
                fragment_data
            )
            fragments.append(fragment)
        if len(fragments) < total_fragments:
            raise RuntimeError("Error while creating fragments: not enough fragments created for the given data and max fragment size.")
        # Create the object and return it.
        return cls(fragments)
    
    def add_fragment(self, fragment: Fragment) -> bool:
        """Adds a fragment to an incomplete BigMessage. Returns whether the addition was successful."""
        # Check if the message is complete already and the fragment has the right id.
        if self.is_complete() or self.id != fragment.message_id:
            return False
        # Check if fragment with this sequence number is already present.
        for f in self.fragments:
            if f.sequence_number == fragment.sequence_number:
                print(f"⚠️ WARNING: Tried to add an already present fragment (sequence number #{fragment.sequence_number}) to a reconstructed BigMessage.")
                return False
        self.fragments.append(fragment)
        return True

    def is_complete(self) -> bool:
        """Whether the BigMessage has all of its frames."""
        return len(self.fragments) == self.total_fragments
    
    def get_payload(self) -> bytes:
        """Returns the entire payload of a complete BigMessage,
        consisting of the concatenation of the contents of the in-order fragments."""

        if not self.is_complete():
            raise RuntimeError(f"Tried to get the payload of an uncomplete BigMessage. ({len(self.fragments)}/{self.total_fragments} fragments present)")
        
        # Sort the fragments based on sequence number and concatenate their contents.
        sorted_fragments = sorted(self.fragments, key=lambda obj: obj.sequence_number)
        complete_message = bytes()
        for fragment in sorted_fragments:
            complete_message += fragment.data
        return complete_message

    def get_fragments(self) -> list[Fragment]:
        return self.fragments


class FragmentingNode:
    def __init__(
            self,
            lora_node: LoRaNode,
            incoming_message_handler = lambda x: x,
    ):
        """Constructs a FragmentingNode.
        Args:
                lora_node: An instantiated LoRaNode
                incoming_message_handler: custom handler that handles complete incoming message payloads."""

        # Use an underlying ReliableCommunicatingNode for sending Fragments.
        self.reliable_communicating_node = ReliableCommunicatingNode(
            lora_node,
            self._handle_received
        )
        self.incomplete_messages: dict[int, BigMessage] = dict() # BigMessage id -> incomplete BigMessage
        self.incoming_message_handler = incoming_message_handler
    
    def send_message(self, large_data: bytes):
        # New id for the message.
        id = self._generate_message_id()
        big_message = BigMessage.from_bytes(id, large_data)
        fragments: list[Fragment] = big_message.get_fragments()

        # Send all fragments one by one for now. For simplicity.
        for (i, fragment) in enumerate(fragments):
            frag_bytes = fragment.serialize()
            try:
                # TODO find good retransmission parameters
                response_tuple = self.reliable_communicating_node.send_reliably_wait_for_answer(frag_bytes)
                response_data = response_tuple[0]
                # Check if the response is as expected an ACK for the sent message.
                expected_ack: bytes = fragment.get_expected_ack_message()
                if response_data != expected_ack:
                    raise RuntimeError(f"Expected an ACK for the sent fragment ({expected_ack}). Instead got: {response_data}")
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
                matching_message.add_fragment(fragment)
            else:
                # This is the first fragment received for this message. This fragment starts a new message reconstruction.
                matching_message: BigMessage = BigMessage([fragment])
                self.incomplete_messages[matching_message.id] = matching_message

            if matching_message.is_complete():
                # Remove the message from the incompleted messages.
                self.incomplete_messages.pop(matching_message.id)
                # Return the completed message to the callback.
                self.incoming_message_handler(matching_message.get_payload())

            # Return ACK for receiving the fragment.
            return fragment.get_expected_ack_message()
            
        except ValueError:
            print(f"⚠️ WARNING: FragmentingNode received a message that couldn't be interpreted as a Fragment: {message_data}. Dropping message.")
            
    
    def _generate_message_id(self) -> int:
        """Generates a random message id for a message to be sent."""
        return random.randint(0, BigMessage.MAX_ID)
