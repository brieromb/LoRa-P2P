import serial
import time

from lora_p2p.lora_kit.serial_helper_code.serial_write_with_confirm import write_with_confirm
from lora_p2p.lora_kit.serial_helper_code.threaded_serial_reader import ThreadedSerialReader

def test_serial_helpers():
    ser1 = serial.Serial(port="COM5", baudrate=9600, timeout=1)
    reader = ThreadedSerialReader(ser1)
    reader.start()

    reader.pause()
    print(write_with_confirm(ser1, b'AT\r\n', b'+AT: OK'))
    print(write_with_confirm(ser1, b'AT+MODE=TEST\r\n', b'+MODE: TEST'))
    print(write_with_confirm(ser1, b'AT+TEST=RXLRPKT\r\n', b'+TEST: RXLRPKT'))
    reader.resume()

    ser2 = serial.Serial(port="COM4", baudrate=9600, timeout=1)
    print(write_with_confirm(ser2, b'AT\r\n', b'+AT: OK'))
    print(write_with_confirm(ser2, b'AT+MODE=TEST\r\n', b'+MODE: TEST'))

    # MULTI LINE EXPECTED RESPONSE TEST
    message = "123456789ABCDEF"
    # Add a 0 in the beginning if the hex message length is uneven
    if len(message)%2 == 1:
        message = "0" + message
    
    command = (f'AT+TEST=TXLRPKT, "{message}"\r\n').encode()
    response = (f'+TEST: TXLRPKT "{message}"\r\n+TEST: TX DONE').encode()
    
    # Send the message from ser2
    print(write_with_confirm(ser2, command, response))

    # Give the response some time to arrive
    time.sleep(3)
    """
    # Read the response from ser1
    try:
        while True:
            data = reader.get_data(timeout=1)
            if data:
                print(f"Got {len(data)} bytes: {data}")
            else:
                print("No data received")
            time.sleep(0.1)
    finally:
        reader.stop()
    """




    
