from typing import final
from received_message_data_handler import ReceivedMessage

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
    def set_on_received_callback(self, callback) -> None:
        self.on_received_callback = callback

    @final
    def send(self, data: bytes):
        """Prepares the node for sending a message by stopping listening,
        then sends the message, and finally resumes listening."""
        # Implement sending logic here
        self._stop_listening() # Stop listening before sending
        self._send_while_not_listening(data) # Send the message
        self._enable_listening() # Resume listening after sending

    def _send_while_not_listening(self, data: bytes) -> None:
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

