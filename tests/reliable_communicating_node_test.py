from lora_p2p import LoRaNode, ReliableCommunicatingNode
import time

def test_reliable_communicating_node():
    # Some end-to-end tests for ReliableCommunicatingNode
    
    node1 = LoRaNode(port="COM4")
    reliable_node1 = ReliableCommunicatingNode(node1)

    # The receiving node is not yet initialized, so this should time out.
    try:
        reliable_node1.send_reliably_wait_for_answer(b"Should not arrive", max_retries=1)
        assert False, "No error was thrown, but the message couldn't have arrived."
    except TimeoutError:
        print("Success: the message that couldn't arrive, did not arrive and correctly threw TimeoutError.")

    # Initialize a second node and do some more tests.
    node2 = LoRaNode(port="COM5")
    reliable_node2 = ReliableCommunicatingNode(node2)

    answer = reliable_node2.send_reliably_wait_for_answer(b"LOL")
    print(f"WAITED FOR AND GOT {answer}")

    reliable_node1.send_reliably(b"HELLO WORLD")
    print("DID SOME WORK WHILE WAITING")
    time.sleep(2)