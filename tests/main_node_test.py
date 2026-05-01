from lora_p2p import MainNode, LoRaNode

def test_main_node():
    def receive_callback1(received):
        message = b'Node 1: Roger that.'
        print(message)
        print(received)
        return message

    def receive_callback2(received):
        message = b'Node 2: Roger that.'
        print(message)
        print(received)
        return message


    node1 = MainNode(LoRaNode(), receive_callback1)
    node2 = MainNode(LoRaNode(), receive_callback2)
    
    node1.send_and_wait(b"DO YOU COPY THIS?AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")