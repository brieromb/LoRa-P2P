from either_listen_or_send_node_interface import ReceivedMessage

class SerialLineProcessor:

    def __init__(self):
        # A message is considered "in the process of being received" if we have received the metadata line (starting with "+TEST: LEN:")
        # but have not yet received the payload line (starting with "+TEST: RX ")
        self.message_getting_processed = None

    def process_line(self, line):
        if line.startswith("+TEST: "):
            line = line[len("+TEST: "):]  # Remove the "+TEST: " prefix for easier processing
            if line.startswith("LEN:"):
                # Process the metadata of the received message. Is received before the payload, so we create a ReceivedMessage object to hold the metadata until the payload is received and we can complete the message.
                parts = line.split(",")  # Split the metadata into parts
                metadata = {}
                for part in parts:
                    key, value = part.split(":")  # Split each part into key and value
                    metadata[key.strip()] = value.strip()  # Store in metadata dictionary
                self.message_getting_processed = ReceivedMessage(metadata)
                return None  # Metadata line does not produce a result yet
            if line.startswith("RX "):
                # Extract the hex payload from the line. The line format is expected to be '+TEST: RX "<hexpayload>"', so we can split by space and take the second part as the hex payload.
                hex_payload = line.split("\"")[1] # Extract the hex payload from the line
                if self.message_getting_processed:
                    self.message_getting_processed.set_payload(hex_payload)
                    finished_message = self.message_getting_processed
                    self.message_getting_processed = None # Reset for the next message
                    return finished_message
                else:
                    print(f"Warning: Received payload without metadata: {line}")
                    message = ReceivedMessage() # Create a message without metadata
                    message.set_payload(hex_payload)
                    return message
            else:
                print(f"Warning: Received non-packet line: {line}")
                return None
        else:
            print(f"Warning: Received non-packet line: {line}")
            return None
