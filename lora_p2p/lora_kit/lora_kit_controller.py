import time

import serial
import string
from .serial_helper_code.threaded_serial_reader import ThreadedSerialReader
from .serial_helper_code.serial_write_with_confirm import write_with_confirm

from ..receiving.received_message_data_parser import ReceivedMessageDataParser


class LoRaKitController:
    """Class that provides a high level interface for sending AT commands to a LoRa module
    over a serial connection, using pyserial."""

    def __init__(self, ser: serial.Serial, received_message_handler=lambda x: print(x)):

        self.ser = ser
        self.received_message_handler = received_message_handler
        
        # Set the callback that handles the received messages
        self.received_message_data_handler = ReceivedMessageDataParser()

        self.threaded_serial_reader = ThreadedSerialReader(
            ser,
            received_line_handler=self.handle_incoming_message_line
        )
        self.threaded_serial_reader.start()

    def check_connection(self) -> bool:
        return self._write_command_and_check_response(b'AT\r\n', b'+AT: OK')
    
    def enable_test_mode(self) -> bool:
        return self._write_command_and_check_response(b'AT+MODE=TEST\r\n', b'+MODE: TEST')
    
    def enable_listening(self) -> bool:
        success = self._write_command_and_check_response(b'AT+TEST=RXLRPKT\r\n', b'+TEST: RXLRPKT')
        if not success:
            raise RuntimeError("Couldn't enter listening mode")
        else:
            # IMPORTANT: resume the listening thread
            self.threaded_serial_reader.resume()
            return success
    
    def send_message(self, payload: bytes):
        # Need to send the payload as a hex string via the AT commands.
        hex_message = payload.hex()
        # Check if the message is a hex string.
        assert all(c in string.hexdigits for c in hex_message)
        # Add a 0 in the beginning if the hex message length is uneven
        if len(hex_message)%2 == 1:
            hex_message = "0" + hex_message
        
        # letters to upper case, because the received response always is received in upper case
        hex_message = hex_message.upper()
        
        command = (f'AT+TEST=TXLRPKT, "{hex_message}"\r\n').encode()
        response = (f'+TEST: TXLRPKT "{hex_message}"\r\n+TEST: TX DONE').encode()
    
        return self._write_command_and_check_response(command, response)

    def handle_incoming_message_line(self, line):
        result = self.received_message_data_handler.process_message_line(line)
        if result:
            # Give the message to the callback that handles the ReceivedMessages.
            self.received_message_handler(result)

    def _write_command_and_check_response(self, command, expected_response) -> bool:
        ####if not self.threaded_serial_reader.is_paused():
        ####    raise RuntimeError("should first pause the threaded serial reader before trying to write a command.")
        self.threaded_serial_reader.pause()

        (success, _, response) = write_with_confirm(self.ser, command, expected_response)

        if not success:
            print(f"⚠️ WARNING: AT command '{command}' got unexpected response: '{response}'. Expected '{expected_response}' instead.")
        return success
    
    def is_listening(self) -> bool:
        return not self.threaded_serial_reader.is_paused()


if __name__ == '__main__':
    ser = serial.Serial('COM4')
    helper = LoRaKitController(ser)

    print(f"Connection OK: {helper.check_connection()}")
    print(f"Test mode OK: {helper.enable_test_mode()}")
    print(f"Listening OK: {helper.enable_listening()}")
    time.sleep(1)


    ser2 = serial.Serial('COM5')
    helper2 = LoRaKitController(ser2)

    print(f"Connection OK: {helper2.check_connection()}")
    print(f"Test mode OK: {helper2.enable_test_mode()}")
    print(f"Sending OK: {helper2.send_message(bytes.fromhex("0123456789ABCDEF"))}")
    time.sleep(1)

    # TODO Check if the message was correctly received


    


