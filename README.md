# LoRa-P2P
A Python interface for using LoRa Wio-E5 Development Kits for reliable Peer to Peer communication.

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
- `SerialHelper`: has high level commands such as check_connection() and enable_listening(). It uses `write_with_confirm` to write a command over the serial connection and also check the response. It also uses a class `ThreadedSerialReader` to monitor the serial port for incoming messages. When a message comes in, it uses a `ReceivedDataMessageHandler` to parse the lines as a `ReceivedMessage`
- `ThreadedSerialReader`: A class that monitors the serial port using a separate thread. It checks periodically after a certain timeout if there is a serial incoming message to be read. When some input is received, the thread handles it using the given callback given from higher up.
