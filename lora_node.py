from typing import override

import serial
from serial_line_processor import SerialLineProcessor
from either_listen_or_send_node_interface import EitherListenOrSendNodeInterface
from threaded_serial_reader import ThreadedSerialReader

def basic_serial_send(ser: serial.Serial, command: str):
    ser.write(command.encode() + b'\r\n')

class LoRaNode(EitherListenOrSendNodeInterface):

    def __init__(self, port, baud=9600):
        self.port = port
    
        self.line_processor = SerialLineProcessor()

        self.serial = serial.Serial(port, baud, timeout=1)

        self.threaded_serial_reader: ThreadedSerialReader = ThreadedSerialReader(self.serial, queue_size=1000)
        # When in listening mode,
        # we want to redirect incoming data to the callback instead of the queue
        self.threaded_serial_reader.set_redirect_data_callback(
            self.receive
        )
        self.threaded_serial_reader.start()
        print(f"SERIAL READER WAS CREATED: {self.threaded_serial_reader}")

        # Setting up the LoRa module
        # Test connection and set to test mode
        basic_serial_send(self.serial, "AT")
        print(f"SERIAL READER IS NOW: {self.threaded_serial_reader}")
        response = self.threaded_serial_reader.get_data(timeout=1)
        print(f"{self.port}: {response}")
        basic_serial_send(self.serial, "AT+MODE=TEST")
        response = self.threaded_serial_reader.get_data(timeout=1)
        print(f"{self.port}: {response}")

        # Set a default callback for received messages, can be overridden by set_on_received_callback
        self.set_on_received_callback_and_start_listening(lambda x: print(f"{port} received: {x}")) 

    @override
    def _send_while_not_listening(self, data):
        basic_serial_send(self.serial, f"AT+TEST=TXLRPKT, {data}")
        response = self.threaded_serial_reader.get_data(timeout=1)
        print(f"{self.port}: {response}")

    @override
    def _enable_listening(self):
        # Set the node to receive mode to listen for incoming packets
        basic_serial_send(self.serial, "AT+TEST=RXLRPKT")
        response = self.threaded_serial_reader.get_data(timeout=1)
        print(f"{self.port}: {response}")
        self.threaded_serial_reader.toggle_redirect_data(True) # Redirect incoming data to the callback instead of the queue

    @override
    def _stop_listening(self):
        # The LoRa module automatically stops listening when a message is sent.
        # But we do need to stop redirecting the data, so that we can look at the response on our commands.
        self.threaded_serial_reader.toggle_redirect_data(False)

    @override
    def is_listening(self):
        return self.threaded_serial_reader.is_redirecting()

