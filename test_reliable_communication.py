from reliable_communicating_node import ReliableCommunicatingNode
from lora_node import LoRaNode

if __name__ == "__main__":
    node1 = LoRaNode("COM4")
    node2 = LoRaNode("COM5")

    reliable_node1 = ReliableCommunicatingNode(node1)
    reliable_node2 = ReliableCommunicatingNode(node2)

    reliable_node1.send_reliably("AABBCCDD")