import threading
from typing import override
import time

from .lora_kit_controller import LoRaKitController, CommunicationParameters
from ..receiving.received_message_data_parser import ReceivedMessage
from ..receiving.received_message import ConnectionQualityMeasurements

class MockMedium:
    """A fake medium over wich MockSerialHelpers can communicate."""

    def __init__(self):
        # TODO: add options to add artificial delay and other parameters.
        self.lora_controllers: list[MockLoRaKitController] = []

    def join(self, lora_controller):
        """Function to let a MockLoRaKitController join the medium.
        This allows it to receive messages from other MockLoRaKitController."""

        self.lora_controllers.append(lora_controller)
    
    def broadcast(self, source, payload: bytes):
        """Broadcast a message payload from a MockLoRaKitController to the others on the medium."""
        # The received hex payload for the real LoRa modules is always in upper case, and if uneven, starts with a zero.
        hex_payload = payload.hex().upper()
        packet_length = len(hex_payload)
        if len(hex_payload) % 2 == 1:
            hex_payload = "0" + hex_payload
            packet_length += 1
        packet_length /= 2 # Packet length is always the hex string length / 2

        # Construct a received message.
        message_to_be_received = ReceivedMessage(
            hexpayload=hex_payload,
            message_length=packet_length,
            conn_qual=ConnectionQualityMeasurements(None, None) # TODO mock these values too in a realistic way.
        )

        for lora_controller in self.lora_controllers:
            if lora_controller == source:
                continue # Don't send to the source

            # Deliver the message using a separate thread.
            messenger_thread = threading.Thread(
                target=self.deliver_message,
                args=(lora_controller, message_to_be_received,)
            )
            messenger_thread.start()
    
    def deliver_message(self, lora_controller, message_to_be_received: ReceivedMessage):
        """Delivers a message to a receiving callback of an LoRaKitController after a small delay.
        Is supposed to be executed in a separate thread."""
        # Add a small transmission delay
        time.sleep(0.05)
        if lora_controller.is_listening():
            lora_controller.received_message_handler(message_to_be_received)
        else:
            raise RuntimeError("The receiving mocked lora controller was not listening while another node tried to deliver a message")


class MockLoRaKitController(LoRaKitController):
    """Class that mocks the behaviour of the LoRaKitController class which controls a LoRa module.
    This can be used for testing purposes without needing to have an actual LoRa module connected via a serial connection."""

    # Medium as a static variable, shared by all LoRaKitController instances.
    medium = MockMedium()

    def __init__(self, received_message_handler=lambda x: print(x)):
        self.test_mode_enabled : bool = False
        self.listening : bool = False
        self.received_message_handler = received_message_handler
        self.medium.join(self)

    @override
    def check_connection(self) -> bool:
        return True

    @override
    def enable_test_mode(self) -> bool:
        self.test_mode_enabled = True

    @override
    def set_communication_parameters(self, params: CommunicationParameters) -> bool:
    
        """The effect of setting the communication parameters isn't mocked.
        Mocked nodes can always communicate with each other, no matter what is configured here."""
        return True

    @override
    def enable_listening(self) -> bool:
        """Enables listening. Can only do this in TEST mode."""

        if not self.test_mode_enabled:
            raise RuntimeError("TEST mode should be enabled before trying to listen.")
        self.listening = True

    @override
    def send_message(self, payload: bytes):
        """Sends a message over the medium. This action disables listening, and can only be done in TEST mode."""
        self.listening = False
        # Broadcast the message in a separate thread, so that it doesn't block the main one
        # It doesn't block either when sending over LoRa.
        messenger_thread = threading.Thread(
            target=self.medium.broadcast,
            args=(self, payload,)
        )
        messenger_thread.start()

    @override
    def handle_incoming_message_line(self, line):
        raise NotImplementedError(
            "This method is skipped in the mocked version." \
            "Messagess are directly given to the callback function as ReceivedMessage instances."
        )

    @override
    def _write_command_and_check_response(self, command, expected_response) -> bool:
        raise NotImplementedError()

    @override
    def is_listening(self) -> bool:
        return self.listening

if __name__ == '__main__':
    lora_controller = MockLoRaKitController()
    lora_controller.check_connection()
    lora_controller.enable_test_mode()
    lora_controller.enable_listening()

    lora_controller2 = MockLoRaKitController()
    lora_controller2.check_connection()
    lora_controller2.enable_test_mode()
    lora_controller2.send_message(b"HELLO WORLD")
    print("Did some work before other received my message")


    




