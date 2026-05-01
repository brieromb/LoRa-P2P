from lora_p2p import FragmentingNode, LoRaNode
from .mock_data import MOCK_LARGE_MESSAGE1, MOCK_LARGE_MESSAGE2
import threading

import json

def test_fragmenting_node():
    _test_multiple_sends_at_same_time()

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
    

    # Convert JSON to bytes and send it.
    json_string = json.dumps(MOCK_LARGE_MESSAGE1, indent=2)
    json_bytes = json_string.encode('utf-8')

    print(f"Sending json file with size {len(json_bytes)} bytes...")
    fragmenting_node1.send_message(json_bytes)

def _test_multiple_sends_at_same_time():
    def _handle_incoming1(incoming_message: bytes):
        json_string_from_bytes = incoming_message.decode('utf-8')
        mock_data_from_bytes = json.loads(json_string_from_bytes)
        print(f"Node1 received: {mock_data_from_bytes}")
    
    def _handle_incoming2(incoming_message: bytes):
        json_string_from_bytes = incoming_message.decode('utf-8')
        mock_data_from_bytes = json.loads(json_string_from_bytes)
        print(f"Node2 received: {mock_data_from_bytes}")

    fragmenting_node1 = FragmentingNode(LoRaNode(), _handle_incoming1)
    fragmenting_node2 = FragmentingNode(LoRaNode(), _handle_incoming2)
    
    # Create threads to send messages in parallel
    def send(sender: FragmentingNode, json_dict: dict):
        # Convert JSON to bytes and send it.
        json_string = json.dumps(json_dict, indent=2)
        json_bytes = json_string.encode('utf-8')
        sender.send_message(json_bytes)
    
    
    # all sends in parallel
    thread1 = threading.Thread(target=send, args=(fragmenting_node1, MOCK_LARGE_MESSAGE2))
    thread2 = threading.Thread(target=send, args=(fragmenting_node2, MOCK_LARGE_MESSAGE2))
    thread3 = threading.Thread(target=send, args=(fragmenting_node1, MOCK_LARGE_MESSAGE1))
    thread4 = threading.Thread(target=send, args=(fragmenting_node2, MOCK_LARGE_MESSAGE1))
    
    
    thread1.start()
    thread2.start()
    thread3.start()
    thread4.start()
    
    # Wait for all to complete
    thread1.join()
    thread2.join()
    thread3.join()
    thread4.join()

def _test_asynchronous_sends():
    # TODO
    pass

    
    

