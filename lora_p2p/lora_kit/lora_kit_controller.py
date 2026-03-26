from dataclasses import dataclass
import time

import serial
import string
from .serial_helper_code.threaded_serial_reader import ThreadedSerialReader
from .serial_helper_code.serial_write_with_confirm import write_with_confirm

from ..receiving.received_message_data_parser import ReceivedMessageDataParser

def _bool_to_on_off_string(bool_value) -> str:
    if bool_value:
        return "ON"
    else:
        return "OFF"

class CommunicationParameters:
    """The communication parameters used to let lora hardware communicate.
    The settings need to be the same on both ends.
    
    Params:
        frequency: in MHz.
        spread_factor: LoRa supports a spread factor of 7 to 12.
        bandwidth: In KHz. Only 125KHz / 250KHz / 500KHz are supported by the hardware.
    
    For the other parameter descriptions, consult the LoRa Wio E5 developer kit documentation or the LoRa standard documentation.
    """
    def __init__(self,
                 frequency = 868,
                 spread_factor = 7,
                 bandwidth = 125,
                 tx_preamble_length = 8,
                 rx_preamble_length = 8,
                 tx_power = 14,
                 crc = True,
                 inverted_iq = False,
                 public_lora_wan = False
    ):  
        self.frequency=frequency
        self.spread_factor=spread_factor
        self.bandwidth=bandwidth
        self.tx_preamble_length=tx_preamble_length
        self.rx_preamble_length=rx_preamble_length
        self.tx_power=tx_power
        self.crc=crc
        self.inverted_iq=inverted_iq
        self.public_lora_wan=public_lora_wan

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
    
    def set_communication_parameters(self, params: CommunicationParameters) -> bool:
    
        """Set the connection parameters. Connection parameters should be the same for two nodes to enable them to communicate.
        Based on this command: AT+TEST=RFCFG,[FREQUENCY],[SF],[BANDWIDTH],[TX PR],[RX PR],[TX POWER],[CRC],[IQ],[NET]
        The default parameters chosen here are for the EU868 MHz band.

        Args:
            frequency: in Hz.
            spread_factor: LoRa supports a spread factor of 7 to 12.
            bandwidth: In KHz. Only 125KHz / 250KHz / 500KHz are supported by the hardware.
        """

        crc_on_off = _bool_to_on_off_string(params.crc)
        inverted_iq_on_off = _bool_to_on_off_string(params.inverted_iq)
        public_lora_wan_on_off = _bool_to_on_off_string(params.public_lora_wan)

        # Construct the AT command
        command = f"AT+TEST=RFCFG, {params.frequency}, SF{params.spread_factor}, {params.bandwidth}, {params.tx_preamble_length}, {params.rx_preamble_length}, {params.tx_power}, {crc_on_off}, {inverted_iq_on_off}, {public_lora_wan_on_off}\r\n"

        response_freq = str(params.frequency) + "000000" # Freq is in Hz in the response for some reason.
        # Construct the expected response
        expected_response = f"+TEST: RFCFG F:{response_freq}, SF{params.spread_factor}, BW{params.bandwidth}K, TXPR:{params.tx_preamble_length}, RXPR:{params.rx_preamble_length}, POW:{params.tx_power}dBm, CRC:{crc_on_off}, IQ:{inverted_iq_on_off}, NET:{public_lora_wan_on_off}"

        return self._write_command_and_check_response(command.encode(), expected_response.encode())

    
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


    


