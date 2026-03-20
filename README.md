# LoRa-P2P
A Python interface for using LoRa Wio-E5 Development Kits for reliable Peer to Peer communication.

## Dependencies
This package only uses the `pyserial` library. It can be installed here: [The official PySerial docs](https://www.pyserial.org/docs)

## How to use
This section goes over the steps necessary to use the package and shows an example usage.

### Preparation
After installing the `pyserial` library you need to find out what the port name is of the port that your LoRa node(s) is/are connected to.
You can do this as follows:
```py
import serial.tools.list_ports

ports = serial.tools.list_ports.comports()
for port in ports:
    print(f"{port.device}: {port.description}")
```
Now that you know the port, you can start sending messages.

### Example
```py
# ====== On a first device ======
def node1_response_to_message(message: bytes) -> bytes:
    if message == b"Hello?":
        return b"Hello!"
    else:
        return b"What??"

node1 = LoRaNode(port="COM4") # This is the port that you explored earlier
reliable_node1 = ReliableCommunicatingNode(node1, node1_response_to_message) # Pass the callback that formulates responses

# ====== On a second device ======
node2 = LoRaNode(port="COM5") # This is the port that you explored earlier
reliable_node2 = ReliableCommunicatingNode(node2) # For this example we keep the default handler

message = b"Hello?"
try:
    answer = reliable_node1.send_reliably_wait_for_answer(message, max_retries=1, retransmission_timeout=0.5)
    print(answer)
except TimeoutError:
    print("The message did not get a reply in the specified amout of tries")
# The reply should be b"Hello!" 
```

## Class structure
class dependencies: 
```
(format: <some_class> -> <classes_it_uses_to_work>)

ReliableCommunicatingNode -> LoRaNode
LoRaNode -> SerialHelper, EitherSendOrListenNodeInterface
SerialHelper -> ThreadedSerialReader, ReceivedDataMessageHandler
```

explanation:
- `ReliableCommunicatingNode`: uses a `LoRaNode` to send and receive messages, but on top of that, uses acknowledgements and retransmissions after a set timeout.
- `LoraNode`: is an implementation of `EitherSendOrListenNodeInterface`. Uses a `SerialHelper` instance to initialise the LoRa module connected via a serial port and to send commands through the serial port to the LoRa device.
- `SerialHelper`: has high level commands such as check_connection() and enable_listening(). It uses `write_with_confirm` to write a command over the serial connection and also check the response. It also uses a class `ThreadedSerialReader` to monitor the serial port for incoming messages. When a message comes in, it uses a `ReceivedDataMessageParser` to parse the lines as a `ReceivedMessage`
- `ThreadedSerialReader`: A class that monitors the serial port using a separate thread. It checks periodically after a certain timeout if there is a serial incoming message to be read. When some input is received, the thread handles it using the given callback given from higher up.
