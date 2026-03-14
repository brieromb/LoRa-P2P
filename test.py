from lora_node import LoRaNode
import time

if __name__ == "__main__":
    node2 = LoRaNode("COM5")
    node2.set_listening(True)
    node1 = LoRaNode("COM4")

    node1.send("AABBCCDD")

    while True:
        time.sleep(1)