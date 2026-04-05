# Peer-to-peer communication using LoRa Wio-E5 Development Kits
This repository provides a Python module interface for communication using LoRa Wio-E5 Development Kits in peer-to-peer TEST mode.
It also provides an example application built on this python module that serves as a http-over-radio tunnel (see `./http_tunnel`)

## Dependencies
**Hardware**: To be able to use this module and its applications, you need at least two [LoRa Wio-E5 Development Kits](https://wiki.seeedstudio.com/LoRa_E5_Dev_Board/) that will communicate with each other.
Though, this module also provides a way to use mocked hardware for local testing.

**Software**: This module is a Python module that only uses the `pyserial` library, which is a library used to communicate with external hardware over a serial port. Here are the official docs of this library: [The official PySerial docs](https://www.pyserial.org/docs)

## How to use
This section goes over the steps necessary to use the package and shows an example usage.

### Finding the port name
You first need to find out what the port name is of the port that your LoRa node(s) is/are connected to.

If you want to locally test the functionality of the code, but you do not have the LoRa kit connected to your PC; You can still execute example code by leaving the port parameter blank. This creates a mock instance of the LoRa module controller that will simulate the behaviour of a controller that is connected to real hardware.

### Example
```py
# ====== On a first device ======

from lora_p2p import *

# Define a custom callback to handle incoming messages
def node1_response_to_message(message_data: tuple[bytes, ConnectionQualityMeasurements]) -> bytes:
    message = message_data[0]
    if message == b"Hello":
        return b"World"
    else:
        return b"What??"

node1 = LoRaNode(port="COM4") # This is the port that you explored earlier
reliable_node1 = ReliableCommunicatingNode(node1, node1_response_to_message) # Pass the callback that formulates responses
```
```py
# ====== On a second device ======

from lora_p2p import *

node2 = LoRaNode(port="COM5") # This is the port that you explored earlier
reliable_node2 = ReliableCommunicatingNode(node2) # For this example we keep the default handler

message = b"Hello"
try:
    answer_data = reliable_node2.send_reliably_wait_for_answer(message, max_retries=1, retransmission_timeout=0.5)
    answer = answer_data[0]
    print(answer)
except TimeoutError:
    print("The message did not get a reply in the specified amout of tries")
# The reply should be b'World'
```
## Peer to peer TEST mode
This is all built upon the P2P functionality of the TEST mode in Wio-E5 Development Kits. These development are originally made for LoRaWAN communication and have limited functionality for peer-to-peer communication.
The TEST mode is the only mode of this hardware kit that allows for P2P communications. So this Python module builds on this.

The TEST mode allows for sending hex strings with a limited length of less than 528 characters. And whenever a node sends a message, it stops listening until listening is explicitly enabled again with an AT command.
More information about these modules in TEST mode can be found in the [official documentation for Wio-E5 Development Kits](https://files.seeedstudio.com/products/317990687/res/LoRa-E5%20AT%20Command%20Specification_V1.0%20.pdf)

### Sending in TEST mode

An example sequence of AT commands sent to the hardware for sending a message:
```
> AT //checking the connection
+AT: OK 

>AT+MODE=TEST //enabling test mode
+MODE: TEST

>AT+TEST=TXLRPKT, "01234556789ABCDEF" //sending a hexadecimal packet
+TEST: TXLRPKT "001234556789ABCDEF"
+TEST: TX DONE
```

### Receiving in TEST mode

An example sequence of AT commands sent to the hardware for enabling listening:
```
> AT //checking the connection
+AT: OK 

>AT+MODE=TEST //enabling test mode
+MODE: TEST

>AT+TEST=RXLRPKT //enabling listening
+TEST: RXLRPKT

//when message received
+TEST: LEN:9, RSSI:-26, SNR:13
+TEST: RX "001234556789ABCDEF"
```

## How it works
Sending the AT commands for sending and receiving in TEST mode happens at the bottom of the stack.
The AT commands are sent by the `LoRaKitController`. This class also checks if the AT command responses are as expected.
It uses some helper classes that use the `pyserial` library for the serial port communication.

The `LoRaNode` abstracts the usage of AT commands, but uses a `LoRaKitController` under the hood.

`ReliableCommunicatingNode` builds on the functionality of a `LoRaNode`, but provides a way to have more reliable communication.
It allows to wait for a response to a sent message. In case of the message getting lost or the response not arriving, this class can also perform retransmissions after a set time, similar to the TCP protocol.
