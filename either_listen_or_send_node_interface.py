from typing import final

class ReceivedMessage:
    def __init__(self, metadata = {}, payload = None):
        self.metadata = metadata # Dictionary to hold metadata key-value pairs
        # The actual payload of the message can be set later too.
        self.payload = None
        if payload is not None:
            self.set_payload(payload)

    def set_payload(self, hexpayload: str):
        self.payload = bytes.fromhex(hexpayload)
    
    def has_payload(self):
        return self.payload is not None
    
    def get_payload(self):
        return self.payload
    
    def __str__(self):
        return f"ReceivedMessage(metadata={self.metadata}, payload={self.payload})"


class EitherListenOrSendNodeInterface:
    """Interface for a node that can either listen or send messages,
    but not both at the same time."""

    def __init__(self):
        pass

    def _enable_listening(self) -> None:
        pass

    def _stop_listening(self) -> None:
        pass

    def is_listening(self) -> bool:
        pass

    @final
    def set_on_received_callback_and_start_listening(self, callback) -> None:
        self.on_received_callback = callback
        self._enable_listening()

    @final
    def send(self, data):
        """Prepares the node for sending a message by stopping listening,
        then sends the message, and finally resumes listening."""
        # Implement sending logic here
        self._stop_listening() # Stop listening before sending
        self._send_while_not_listening(data) # Send the message
        self._enable_listening() # Resume listening after sending

    def _send_while_not_listening(self, data) -> None:
        pass

    @final
    def receive(self, message: ReceivedMessage):
        """Handles receiving a message. This should only be called when the node is in listening mode."""
        # Implement receiving logic here
        if not self.is_listening():
            print("Cannot receive while not listening.")
            return
        if self.on_received_callback:
            self.on_received_callback(message)
        else:
            print("Received a message, but no callback is set.")

