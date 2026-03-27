from dataclasses import dataclass


@dataclass
class ConnectionQualityMeasurements:
    """The connection quality measurements measured when receiving a single message.
    
    Params:
        rssi: received signal strength indicator. in dBm.
        snr: signal to noise ratio. in dB."""

    rssi: int
    snr: int

    def __str__(self):
        return f"<RSSI: {self.rssi}dBm, SNR: {self.snr}dB>"
    
    def __repr__(self):
        return self.__str__()

class ReceivedMessage:
    """Represents a message received by a LoRa kit in listening mode.
    
    Params:
        payload: the message payload in bytes.
        message_length: length of the message, measured in #TODO
        conn_qual: the connection quality measurements measured when receiving this message."""

    def __init__(self, message_length: int, conn_qual: ConnectionQualityMeasurements, hexpayload: str|None = None):
        self.conn_qual = conn_qual
        self.message_length = message_length # Dictionary to hold metadata key-value pairs
        # The actual payload of the message can be set later too.
        self.payload = None
        if hexpayload is not None:
            self.set_payload(hexpayload)

    def set_payload(self, hexpayload: str):
        self.payload = bytes.fromhex(hexpayload)
    
    def has_payload(self):
        return self.payload is not None
    
    def get_payload(self) -> bytes:
        return self.payload

    def get_message_length(self) -> int:
        return self.message_length
    
    def get_connection_quality(self) -> ConnectionQualityMeasurements:
        return self.conn_qual
    
    def as_tuple(self):
        """Returns a tuple containing the message payload and the connection quality measurements for this message.
        This class will not be exposed to the end user, but the tuple representation will.
        """
        return (self.get_payload(), self.get_connection_quality())
     
    def __str__(self):
        return str(self.as_tuple())