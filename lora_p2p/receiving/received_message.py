class ReceivedMessage:
    def __init__(self, metadata = {}, hexpayload = None):
        self.metadata = metadata # Dictionary to hold metadata key-value pairs
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
    
    def __str__(self):
        return f"ReceivedMessage(metadata={self.metadata}, payload={self.payload})"
