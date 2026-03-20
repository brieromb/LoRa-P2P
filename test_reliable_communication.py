from reliable_communicating_node import ReliableCommunicatingNode
from lora_node import LoRaNode

if __name__ == "__main__":
    node1 = LoRaNode(port="COM4", baud=9600)
    node2 = LoRaNode(port="COM5", baud=9600)

    reliable_node1 = ReliableCommunicatingNode(node1)
    reliable_node2 = ReliableCommunicatingNode(node2)

    reliable_node1.send_reliably("HELLO WORLD".encode("utf-8"))