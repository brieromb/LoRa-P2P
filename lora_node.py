import threading

import serial
import time
from serial_helper_commands import send_command_read_response
from serial_line_processor import SerialLineProcessor

class LoRaNode:

    def __init__(self, port, baud=9600):
        self.port = port
        self.line_processor = SerialLineProcessor()
        self.serial = serial.Serial(port, baud, timeout=1)
        self.listening_thread = None
        self.stop_listening = threading.Event() # Flag to signal the listening thread to stop
        self.on_received = lambda x: print(f"Received: {x}") # Default callback for received messages, can be overridden by set_on_received_callback

        # Setting up the LoRa module
        # Test connection and set to test mode
        response = send_command_read_response(self.serial, "AT")
        print(f"{self.port}: {response}")
        response = send_command_read_response(self.serial, "AT+MODE=TEST")
        print(f"{self.port}: {response}")

        # Set the node to receive mode to listen for incoming packets
        self._set_listening(True)
    
    def send(self, data):
        self._set_listening(False)  # Cannot listen while sending
        response = send_command_read_response(self.serial, f"AT+TEST=TXLRPKT, {data}")
        print(f"{self.port}: {response}")
        self._set_listening(True)  # Resume listening
    
    def set_on_received_callback(self, callback):
        self.on_received = callback
    
    def _set_listening(self, listening: bool):
        if listening:
            self.stop_listening.clear()
            # Set the node to receive mode to listen for incoming packets
            response = send_command_read_response(self.serial, "AT+TEST=RXLRPKT")
            print(f"{self.port}: {response}")
            # Start listening to the serial stream in a separate thread
            self.listening_thread = threading.Thread(target=self._process_serial_stream)
            self.listening_thread.start()
        else:
            self.stop_listening.set()
            self.listening_thread.join()
            self.listening_thread = None

    def _process_serial_stream(self):
        """Listen for incoming packets and process them
        Based on the official pyserial docs: https://www.pyserial.org/docs/reading-data
        """
        line_buffer = b''
        
        while not self.stop_listening.is_set():
            try:
                # Read available data
                if self.serial.in_waiting:
                    chunk = self.serial.read(self.serial.in_waiting)
                    line_buffer += chunk
                    
                    # Process complete lines
                    while b'\n' in line_buffer:
                        line, line_buffer = line_buffer.split(b'\n', 1)
                        try:
                            text = line.decode('utf-8').strip()
                            if text:
                                result = self.line_processor.process_line(text)
                                if result:
                                    self.on_received(result)
                        except Exception as e:
                            print(f"Process error: {e}")
                else:
                    time.sleep(0.1) # Sleep time can be way higher. Lines don't get lost due to sleeping because there is a serial buffer. 
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Stream error: {e}")
    

    
