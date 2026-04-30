from lora_p2p import FragmentingNode, LoRaNode

def test_fragmenting_node():
    def _handle_incoming1(incoming_message: bytes):
        print(f"Node1 received: {incoming_message}")
        return b""
    
    def _handle_incoming2(incoming_message: bytes):
        print(f"Node2 received: {incoming_message}")
        return b""

    fragmenting_node1 = FragmentingNode(LoRaNode(), _handle_incoming1)
    fragmenting_node2 = FragmentingNode(LoRaNode(), _handle_incoming2)
    
    fragmenting_node1.send_message(b'Not a large message at all.')

    

