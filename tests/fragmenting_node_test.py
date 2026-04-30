from lora_p2p import FragmentingNode, LoRaNode

import json

def test_fragmenting_node():
    _test_large_json()

def _test_small_message():
    def _handle_incoming1(incoming_message: bytes):
        print(f"Node1 received: {incoming_message}")
    
    def _handle_incoming2(incoming_message: bytes):
        print(f"Node2 received: {incoming_message}")

    fragmenting_node1 = FragmentingNode(LoRaNode(), _handle_incoming1)
    fragmenting_node2 = FragmentingNode(LoRaNode(), _handle_incoming2)
    
    fragmenting_node1.send_message(b'Not a large message at all.')

def _test_large_json():
    def _handle_incoming_raw_json(incoming_message: bytes):
        json_string_from_bytes = incoming_message.decode('utf-8')
        mock_data_from_bytes = json.loads(json_string_from_bytes)
        print(mock_data_from_bytes)
    
    fragmenting_node1 = FragmentingNode(LoRaNode())
    fragmenting_node2 = FragmentingNode(LoRaNode(), _handle_incoming_raw_json)
    
    # Some random mock JSON data to show it works for larger files.
    mock_data = {
        "users": [
            {
                "id": 1,
                "name": "John Doe",
                "email": "john@example.com",
                "is_active": True,
                "age": 30,
                "preferences": {
                    "theme": "dark",
                    "notifications": False
                }
            },
            {
                "id": 2,
                "name": "Jane Smith",
                "email": "jane@example.com",
                "is_active": False,
                "age": 25,
                "preferences": {
                    "theme": "light",
                    "notifications": True
                }
            }
        ],
        "total_users": 2,
        "version": "1.0.0"
    }

    # Convert JSON to bytes and send it.
    json_string = json.dumps(mock_data, indent=2)
    json_bytes = json_string.encode('utf-8')

    print(f"Sending json file with size {len(json_bytes)} bytes...")
    fragmenting_node1.send_message(json_bytes)

def _test_multiple_sends_at_same_time():
    def _handle_incoming1(incoming_message: bytes):
        print(f"Node1 received: {incoming_message}")
    
    def _handle_incoming2(incoming_message: bytes):
        print(f"Node2 received: {incoming_message}")

    fragmenting_node1 = FragmentingNode(LoRaNode(), _handle_incoming1)
    fragmenting_node2 = FragmentingNode(LoRaNode(), _handle_incoming2)
    
    fragmenting_node1.send_message(b'Not a large message at all.')
    fragmenting_node2.send_message(b'some other message')
    fragmenting_node1.send_message(b'another one')

def _test_asynchronous_sends():
    # TODO
    pass

    
    

