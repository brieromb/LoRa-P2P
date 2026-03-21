from typing import override

import serial
from either_listen_or_send_node_interface import EitherListenOrSendNodeInterface
from at_commander import ATCommander
from mock_at_commander import MockATCommander

class LoRaNode(EitherListenOrSendNodeInterface):

    def __init__(self, port: None | str = None):
        """Creates an instance of a LoRaNode.
        
        Args:
            port: the name of the physical port that the LoRa Wio-E5 Development Kit is connected to.
                If this is None, a mock version of a LoRa node is created that doesn't use real hardware."""

        if port is None:
            # Create a mocked version of the AT commander. This works without real hardware.
            self.serial_helper = MockATCommander(received_message_handler=self.receive)
        else:
            # Use real hardware connected at the specified port.
            ser = serial.Serial(port, baudrate=9600, timeout=1)
            self.serial_helper = ATCommander(ser, received_message_handler=self.receive)
        
        # Setting up the LoRa module
        # Test connection and set to test mode
        self.serial_helper.check_connection()
        self.serial_helper.enable_test_mode()
        self.serial_helper.enable_listening()

    @override
    def _send_while_not_listening(self, data: bytes):
        self.serial_helper.send_message(data)

    @override
    def _enable_listening(self):
        self.serial_helper.enable_listening()
    
    @override
    def _stop_listening(self):
        # The LoRa module automatically stops listening when a message is sent.
        # So we don't need to do anything here
        pass

    @override
    def is_listening(self):
        return self.serial_helper.is_listening()

