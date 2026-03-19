import time

from lora_node import LoRaNode

if __name__ == "__main__":
    node1 = LoRaNode("COM4")
    time.sleep(2)  # Give the nodes some time to set up and start listening
    node2 = LoRaNode("COM5")

    time.sleep(2)  # Give the nodes some time to set up and start listening
    node1.send("AABBCCDD")
