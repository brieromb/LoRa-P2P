from .received_message import ReceivedMessage, ConnectionQualityMeasurements

class ReceivedMessageDataParser:
    """Handles incoming message data lines. A message consists of 2 lines:

        +TEST: LEN:<length>, RSSI:<rssi>, SNR:<snr>

        +TEST: RX "<message>
    
        The lines always arrive in that order. So we make use of that.
        First we expect message metadata to arrive, then the payload.
        When the message is complete, it is returned as an instance of ReceivedMessage.
    """
    
    def __init__(self):
        self.message_getting_processed = None

    def process_message_line(self, message_line) -> ReceivedMessage | None:
        if self.message_getting_processed is None:
            # No message is already getting processed. So this line must be message metadata.
            metadata = self._parse_metadata(message_line)
            if not metadata:
                return
            # Add the metadata to the newly received message.
            conn_qual_measurements = ConnectionQualityMeasurements(metadata["RSSI"], metadata["SNR"])
            message_length = metadata["LEN"]
            self.message_getting_processed = ReceivedMessage(message_length, conn_qual_measurements)
            # A new message is getting processed. Wait for the payload before returning it.
            return
        else:
            # A message with metadata was already processed. So this must be the payload.
            payload = self._parse_payload(message_line)
            if not payload:
                return
            self.message_getting_processed.set_payload(payload)
            # Return the finished message, and reset the current message being handled.
            finished_message = self.message_getting_processed
            self.message_getting_processed = None
            return finished_message
            
    
    def _parse_metadata(self, metadata_line) -> dict | None:
        """Handles a message line like:
        
        +TEST: LEN:<length>, RSSI:<rssi>, SNR:<snr>

        and extracts the metadata from it.
        """
        try: 
            metadata_line = metadata_line[len("+TEST: "):]  # Remove the "+TEST: " prefix for easier processing
            parts = metadata_line.split(",")
            metadata = {}
            for part in parts:
                key, value = part.split(":")  # Split each part into key and value
                metadata[key.strip()] = int(value.strip())  # Store in metadata dictionary
            return metadata
        except Exception:
            print(f"⚠️ WARNING: tried to parse a serial line as message metadata, but got: {metadata_line}")
            return None


    def _parse_payload(self, payload_line):
        """Handles a message line like:
        
        +TEST: RX "<message>"

        and extracts the payload from it.
        """
    
        splitted = payload_line.split("\"")
        if len(splitted) < 2:
            print(f"⚠️ WARNING: tried to parse a serial line as message payload, but got: {payload_line}")
            return None
        else:
            return splitted[1]