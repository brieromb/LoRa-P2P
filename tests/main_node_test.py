from lora_p2p import MainNode, LoRaNode

def test_main_node():
    def receive_callback1(received):
        message = b'Node 1: Roger that.'
        print(f"Node 1: sending response: {message}")
        print(received)
        return message

    def receive_callback2(received):
        message = b'Node 2: Roger that.'
        print(f"Node 2: sending response: {message}")
        print(received)
        return message


    node1 = MainNode(LoRaNode("COM4"), receive_callback1, 3, 0.5)
    node2 = MainNode(LoRaNode("COM5"), receive_callback2, 3, 0.5)
    
    response = node1.send_and_wait(b"DO YOU COPY THIS?ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789101112131415161718192021222324252627282930313233343536373839404142")
    print(f"DONE!!!!! Received response: {response}")