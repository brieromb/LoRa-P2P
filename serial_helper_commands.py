"""
This file contains example code from the official docs of the pyserial library.
https://www.pyserial.org/docs/reading-data
"""

import time

def send_command_read_response(ser, command, timeout=2):
    """Send command and read response reliably"""
    # Clear any pending data
    ser.reset_input_buffer()
    
    # Send command
    ser.write(command.encode() + b'\r\n')
    
    # Read response with timeout
    old_timeout = ser.timeout
    ser.timeout = timeout
    
    try:
        response = ser.readline()
        return response.decode('utf-8').strip()
    finally:
        ser.timeout = old_timeout

def process_serial_stream(ser, line_processor):
    """Process continuous serial data stream"""
    line_buffer = b''
    
    while True:
        try:
            # Read available data
            if ser.in_waiting:
                chunk = ser.read(ser.in_waiting)
                line_buffer += chunk
                
                # Process complete lines
                while b'\n' in line_buffer:
                    line, line_buffer = line_buffer.split(b'\n', 1)
                    try:
                        text = line.decode('utf-8').strip()
                        if text:
                            result = line_processor(text)
                            if result:
                                yield result
                    except Exception as e:
                        print(f"Process error: {e}")
            else:
                time.sleep(0.001)
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Stream error: {e}")