import time

class ConnectionQualityMeasurements():
    """The connection quality measurements measured when receiving a single message.
    
    Params:
        rssis: list of received signal strength indicator. in dBm.
        snrs: list of signal to noise ratio. in dB.
        times: list of times at which these were measured. in seconds elapsed since the Epoch."""

    rssis: list[int]
    snrs: list[int]
    times: list[float]

    def __init__(self, rssi: int | None = None, snr: int | None = None, time: float = time.time()):
        """Creates a connectionQualityMeasurements instance. If rssi or snr are None, an empty instance is created."""
        self.rssis = []
        self.snrs = []
        self.times = []
        if rssi is not None and snr is not None:
            self.rssis.append(rssi)
            self.snrs.append(snr)
            self.times.append(time)

    def __str__(self):
        s = "["
        for i in range(len(self.rssis)):
            s += f" <RSSI: {self.rssis[i]}dBm, SNR: {self.snrs[i]}dB>"
        s += " ]"
        return s
    
    def __iadd__(self, other):
        """measurements += other_measuremens combines the measurements into the first object."""
        self.rssis += other.rssis
        self.snrs += other.snrs
        self.times += other.times
        return self
    
    def __add__(self, other):
        pass
    
    def get_data(self) -> dict:
        data_dict = dict()
        data_dict["rssis"] = self.rssis
        data_dict["snrs"] = self.snrs
        data_dict["times"] = self.times
        return data_dict
    
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