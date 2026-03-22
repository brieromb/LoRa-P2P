import serial

from .lora_kit.lora_kit_controller import LoRaKitController
from .lora_kit.mock_lora_kit_controller import MockLoRaKitController
from .receiving.received_message_data_parser import ReceivedMessage

class LoRaNode:
    """A high level communicating node that uses a LoRaKitController to take care of switching modes and setting up the hardware.
    Can send messages to other nodes and also handles incoming ReceivedMessages from other nodes."""

    def __init__(self, port: None | str = None):
        """Creates an instance of a LoRaNode.
        
        Args:
            port: the name of the physical port that the LoRa Wio-E5 Development Kit is connected to.
                If this is None, a mock version of a LoRa node is created that doesn't use real hardware."""

        if port is None:
            # Create a mocked version of the LoRaKitController. This works without real hardware.
            self.lora_controller = MockLoRaKitController(received_message_handler=self.receive)
        else:
            # Use real hardware connected at the specified port.
            ser = serial.Serial(port, baudrate=9600, timeout=1)
            self.lora_controller = LoRaKitController(ser, received_message_handler=self.receive)
        
        # Setting up the LoRa module
        # Test connection and set to test mode
        self.lora_controller.check_connection()
        self.lora_controller.enable_test_mode()
        self.lora_controller.enable_listening()

    def set_on_received_callback(self, callback) -> None:
        self.on_received_callback = callback

    def send(self, data: bytes):
        """Sends a message, which disables listening.
        Resumes listening after finishing sending"""

        self.lora_controller.send_message(data) # Send the message, which disables listening.
        self.lora_controller.enable_listening() # Resume listening after sending

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

    def is_listening(self):
        return self.lora_controller.is_listening()

