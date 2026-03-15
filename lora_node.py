import threading

import serial
import time
from serial_helper_commands import send_command_read_response

class LoRaNode:

    def __init__(self, port, baud=9600):
        self.port = port
        self.serial = serial.Serial(port, baud, timeout=1)
        self.template_line_processor = lambda x: f"{self.port}: {x}"
        self.listening_thread = None
        self.stop_listening = threading.Event() # Flag to signal the listening thread to stop

        # Setting up the LoRa module
        # Test connection and set to test mode
        response = send_command_read_response(self.serial, "AT")
        print(f"{self.port}: {response}")
        response = send_command_read_response(self.serial, "AT+MODE=TEST")
        print(f"{self.port}: {response}")

        # Set the node to receive mode to listen for incoming packets
        self.set_listening(True)

    def lora_line_processor(self, line):
        if line.startswith("+TEST: RX "):
            print(f"{self.port}: Received test packet: {line}")
            return line
        else:
            print(f"{self.port}: Received non-packet line: {line}")
            return None
    
    def send(self, data):
        self.set_listening(False)  # Cannot listen while sending
        response = send_command_read_response(self.serial, f"AT+TEST=TXLRPKT, {data}")
        print(f"{self.port}: {response}")
        self.set_listening(True)  # Resume listening
    
    def set_listening(self, listening: bool):
        if listening:
            self.stop_listening.clear()
            # Set the node to receive mode to listen for incoming packets
            response = send_command_read_response(self.serial, "AT+TEST=RXLRPKT")
            print(f"{self.port}: {response}")
            # Start listening to the serial stream in a separate thread
            self.listening_thread = threading.Thread(target=self.process_serial_stream)
            self.listening_thread.start()
        else:
            self.stop_listening.set()
            self.listening_thread.join()
            self.listening_thread = None

    def process_serial_stream(self):
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
                                result = self.template_line_processor(text)
                                if result:
                                    print(result)
                                    #yield result
                        except Exception as e:
                            print(f"Process error: {e}")
                else:
                    time.sleep(0.001)
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Stream error: {e}")
    

    
