from lora_p2p import MainNode, LoRaNode

def test_main_node():
    def receive_callback1(_: bytes):
        message = b'Node 1: Roger that.'
        print(message)
        return message

    def receive_callback2(_: bytes):
        message = b'Node 2: Roger that.'
        print(message)
        return message


    node1 = MainNode(LoRaNode(), receive_callback1)
    node2 = MainNode(LoRaNode(), receive_callback2)
    
    node1.send_and_wait(b"DO YOU COPY THIS?AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")