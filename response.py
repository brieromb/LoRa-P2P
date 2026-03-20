import pickle

from received_message_data_parser import ReceivedMessage

class Response:
    """A response is a class that represents a message response to a previously sent message.
    A Response instance is sent over the medium, encoded as bytes."""

    def __init__(self, response_for: bytes | ReceivedMessage, response_contents: bytes):
        assert isinstance(response_for, bytes) or isinstance(response_for, ReceivedMessage), "response_for should be either bytes or a ReceivedMessage instance"
        if isinstance(response_for, ReceivedMessage):
            self.response_for = response_for.get_payload()
        else: 
            self.response_for = response_for
        self.response_contents = response_contents

    @staticmethod
    def from_bytes(bytes_response):
        """Tries to convert a response from raw bytes. If this didn't work None is retured."""
        try: 
            dict_instance: dict = pickle.loads(bytes_response)
            # Check if the received dict is convertible to a response
            if isinstance(dict_instance, dict):
                response_for_field = dict_instance.get('response_for')
                response_contents_field = dict_instance.get('response_contents')
                if len(dict_instance) == 2 and response_for_field is not None and response_contents_field is not None:
                    return Response(
                        response_for=response_for_field,
                        response_contents=response_contents_field
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
        return self.response_for == earlier_message

    def as_bytes(self):
        response_dict = {'response_for': self.response_for, 'response_contents': self.response_contents}
        return pickle.dumps(response_dict)
    
    def get_original_message(self) -> bytes:
        """Get the message that this response responded to."""
        return self.response_for
    
    def __repr__(self):
        return f"Response({self.response_for},{self.response_contents})"

if __name__ == '__main__':
    # Test if a response can be converted into bytes and back.
    message_payload = b'HELLO WORLD'
    response_payload = b'HELLO'

    response = Response(message_payload, response_payload)
    bytes_response = response.as_bytes()

    response2 = Response.from_bytes(bytes_response)

    assert response2.is_response_for(message_payload)
    print("Success")

    # Test if a Response can be created from a ReceivedMessage.
    message = ReceivedMessage({}, message_payload.hex())
    response = Response(message, response_payload)
    assert response.is_response_for(message.get_payload())
    print("Success")

    assert Response.from_bytes(message_payload) is None
    print("Success")

