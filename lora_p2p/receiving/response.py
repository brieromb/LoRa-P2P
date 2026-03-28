import pickle
import hashlib

from .received_message_data_parser import ReceivedMessage

class ResponsePayload:
    """Represents a response payload to a previously sent message.
    A response is sent over the medium as a dict like:
    
    {response_for: <bytes>, response_contents: <bytes>} (but encoded as bytes)

    And when a message is received, it is decoded and checked if it is of the format expected from a response payload. 
    """

    # The length of the identifier for the message.
    # The fingerprint is sent together with the response,
    # so that the response can be linked back to the original message it responds to.
    MESSAGE_FINGERPRINT_LENGTH = 4

    def __init__(
            self,
            response_for: bytes | ReceivedMessage,
            response_contents: bytes,
            _digest_provided: bool = False
    ):
        """Create a ResponsePayload instance.
        At the sender side this is constructed from the original message and the response payload.
        At the receiver side this is constructed using the digest.
        
        Args:
            response_for: The original message (`bytes` or `ReceivedMessage`) or the message digest (`bytes`).
                In case that the message digest is provided, `_digest_provided` should be True.
            response_contents: The response payload in bytes.
            _digest_provided: Whether the `response_for` field is already a message digest."""

        assert isinstance(response_for, bytes) or isinstance(response_for, ReceivedMessage), "response_for should be either bytes or a ReceivedMessage instance"
        if isinstance(response_for, ReceivedMessage):
            response_for = response_for.get_payload()
        
        if _digest_provided:
            # The response_for field contains message digest.
            self.original_message_digest = response_for
        else:
            # Convert the original message to a digest.
            self.original_message_digest = self._calculate_message_digest(response_for)

        self.response_contents = response_contents

    @staticmethod
    def from_bytes(bytes_response):
        """Tries to convert a response from raw bytes. If this didn't work None is retured."""
        try: 
            dict_instance: dict = pickle.loads(bytes_response)
            # Check if the received dict is convertible to a response
            if isinstance(dict_instance, dict):
                original_message_digest_field = dict_instance.get('original_message_digest')
                response_contents_field = dict_instance.get('response_contents')
                if len(dict_instance) == 2 and original_message_digest_field is not None and response_contents_field is not None:
                    return ResponsePayload(
                        response_for=original_message_digest_field,
                        response_contents=response_contents_field,
                        _digest_provided=True # IMPORTANT. If this was not set, the message digest would get hashed again.
                    )
                else:
                    print(f"⚠️ WARNING: A response was received, but it could not be interpreted. Got: {dict_instance}")
                    return None
            else:
                return None
        except pickle.UnpicklingError: # Can be thrown by the pickle.loads().
            # So if the load didn't work, the message is probably not a response.
            return None

    def is_response_for(self, earlier_message: bytes) -> bool:
        """Check if this response was a response for a certain earlier message."""
        # Hash the earlier message and compare the hash values
        expected_digest = self._calculate_message_digest(earlier_message)
        return self.original_message_digest == expected_digest

    def as_bytes(self):
        response_dict = {'original_message_digest': self.original_message_digest, 'response_contents': self.response_contents}
        return pickle.dumps(response_dict)
    
    def get_original_message_digest(self) -> bytes:
        """Get the digest of the message that this response responded to."""
        return self.original_message_digest
    
    def get_contents(self) -> bytes:
        return self.response_contents
    
    def _calculate_message_digest(self, message: bytes) -> bytes:
        h = hashlib.blake2b(message, digest_size=self.MESSAGE_FINGERPRINT_LENGTH)
        return h.digest()


if __name__ == '__main__':
    # Test if a response can be converted into bytes and back.
    message_payload = b'HELLO WORLD'
    response_payload = b'HELLO'

    response = ResponsePayload(message_payload, response_payload)
    bytes_response = response.as_bytes()

    response2 = ResponsePayload.from_bytes(bytes_response)

    assert response2.is_response_for(message_payload)
    print("Success")

    # Test if a Response can be created from a ReceivedMessage.
    message = ReceivedMessage({}, message_payload.hex())
    response = ResponsePayload(message, response_payload)
    assert response.is_response_for(message.get_payload())
    print("Success")

    assert ResponsePayload.from_bytes(message_payload) is None
    print("Success")

