from typing import override

import serial
from either_listen_or_send_node_interface import EitherListenOrSendNodeInterface
from lora_kit_controller import LoRaKitController
from mock_lora_kit_controller import MockLoRaKitController

class LoRaNode(EitherListenOrSendNodeInterface):
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

    @override
    def _send_while_not_listening(self, data: bytes):
        self.lora_controller.send_message(data)

    @override
    def _enable_listening(self):
        self.lora_controller.enable_listening()
    
    @override
    def _stop_listening(self):
        # The LoRa module automatically stops listening when a message is sent.
        # So we don't need to do anything here
        pass

    @override
    def is_listening(self):
        return self.lora_controller.is_listening()

