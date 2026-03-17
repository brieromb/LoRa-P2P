import time
import serial

def write_with_confirm(ser, data, expected_response=b'OK', timeout=2):
    """Write data and wait for confirmation see https://www.pyserial.org/docs/writing-data"""
    # Clear input buffer
    ser.reset_input_buffer()
    
    # Send data
    bytes_written = ser.write(data)
    ser.flush()  # Force transmission
    
    # Wait for confirmation
    start_time = time.time()
    response = b''
    
    while time.time() - start_time < timeout:
        if ser.in_waiting:
            chunk = ser.read(ser.in_waiting)
            response += chunk
            
            if expected_response in response:
                return True, bytes_written, response
        
        time.sleep(0.01)
    
    return False, bytes_written, response

if __name__ == '__main__':
    # TEST EXAMPLE USAGE
    ser = serial.Serial(port="COM4", baudrate=9600, timeout=1)
    print(write_with_confirm(ser, b'AT\r\n', b'+AT: OK'))
    print(write_with_confirm(ser, b'AT+MODE=TEST\r\n', b'+MODE: TEST'))

    # MULTI LINE EXPECTED RESPONSE TEST
    message = "123456789ABCDEF"
    # Add a 0 in the beginning if the hex message length is uneven
    if len(message)%2 == 1:
        message = "0" + message
    
    command = (f'AT+TEST=TXLRPKT, "{message}"\r\n').encode()
    response = (f'+TEST: TXLRPKT "{message}"\r\n+TEST: TX DONE').encode()

    print(write_with_confirm(ser, command, response))

    
    