from .receiving.received_message import ConnectionQualityMeasurements

class Fragment:
    """A serialized fragment of a message, with fields:
    | msg_id | total_frags | seq_num | payload_len | data |
    """
    MESSAGE_ID_BYTES = 4
    TOTAL_FRAGS_BYTES = 3
    SEQ_NUM_BYTES = TOTAL_FRAGS_BYTES

    TOTAL_HEADER_LEN = MESSAGE_ID_BYTES + TOTAL_FRAGS_BYTES + SEQ_NUM_BYTES
    MAX_PAYLOAD_SIZE = 224 # TODO derive this from hardware limit.

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
        data = bytes_data[Fragment.MESSAGE_ID_BYTES + Fragment.TOTAL_FRAGS_BYTES + Fragment.SEQ_NUM_BYTES:]
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

        # Keep the connection quality measurements for the whole transmission of this message
        self.conn_qual_meas: ConnectionQualityMeasurements = ConnectionQualityMeasurements()

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
    
    def add_fragment(self, fragment: Fragment, conn_qual_meas: ConnectionQualityMeasurements) -> bool:
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
        self.conn_qual_meas += conn_qual_meas # Add the connection quality measurements
        return True

    def is_complete(self) -> bool:
        """Whether the BigMessage has all of its frames."""
        return len(self.fragments) == self.total_fragments
    
    def get_payload_tuple(self) -> tuple[bytes, ConnectionQualityMeasurements]:
        """Returns the entire payload of a complete BigMessage,
        consisting of the concatenation of the contents of the in-order fragments."""

        if not self.is_complete():
            raise RuntimeError(f"Tried to get the payload of an uncomplete BigMessage. ({len(self.fragments)}/{self.total_fragments} fragments present)")
        
        # Sort the fragments based on sequence number and concatenate their contents.
        sorted_fragments = sorted(self.fragments, key=lambda obj: obj.sequence_number)
        complete_message = bytes()
        for fragment in sorted_fragments:
            complete_message += fragment.data
        return (complete_message, self.conn_qual_meas)

    def get_fragments(self) -> list[Fragment]:
        return self.fragments