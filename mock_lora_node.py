from either_listen_or_send_node_interface import EitherListenOrSendNodeInterface

class MockLoRaNode(EitherListenOrSendNodeInterface):
    """A mock implementation of the EitherListenOrSendNodeInterface for testing purposes."""

    def __init__(self):
        self._enable_listening()

    def _enable_listening(self) -> None:
        self._listening = True
        print("MockLoRaNode: Listening enabled.")

    def _send_while_not_listening(self, data) -> None:
        print(f"MockLoRaNode: Sending message '{data}'")

    def _stop_listening(self) -> None:
        self._listening = False
        print("MockLoRaNode: Listening stopped.")

    def is_listening(self) -> bool:
        return self._listening