from typing import override

from ..transmission import Transmission

from .response_payload import ResponsePayload
from .received_message import ReceivedMessage


class ReceivedResponse(ReceivedMessage):
    def __init__(self, from_message: ReceivedMessage):
        """Tries to interpret a ReceivedMessage as a ReceivedResponse.
        Raises ValueError when the ReceivedMessage cannot be interpreted as a response."""

        # First check if the received message can be interpreted as a response.
        payload = from_message.get_payload()
        response_payload = ResponsePayload.from_bytes(payload)
        if response_payload is None:
            raise ValueError("The ReceivedMessage could not be interpreted as a response.")

        # Successfully interpreted the message as a response.
        # Now set the fields of this ReceivedResponse.
        self.conn_qual = from_message.conn_qual
        self.payload = response_payload

    @override
    def set_payload(self, hexpayload):
        raise NotImplementedError("This function should not be called, because the payload should be set when creating an instance of this class.")
    
    @override
    def get_payload(self):
        return self.payload.get_contents()
    
    def finishes_transmission(self, transmission: Transmission) -> bool:
        """Returns if this response finishes the transmission.
        This is the case when the response responds to the sent data of the transmission."""
    
        return self.payload.is_response_for(transmission.get_send_data())
    
    def get_original_message_digest(self):
        return self.payload.get_original_message_digest()
    
    def __str__(self):
        return f"{self.payload.get_original_message_digest()} <- " + super().__str__()



    