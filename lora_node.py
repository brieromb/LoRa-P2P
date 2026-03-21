from typing import override

import serial
from either_listen_or_send_node_interface import EitherListenOrSendNodeInterface
from at_commander import ATCommander

class LoRaNode(EitherListenOrSendNodeInterface):

    def __init__(self, port, baud=9600):
        self.port = port

        ser = serial.Serial(port, baud, timeout=1)

        # Set the received message handler to the receive function of this class
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

