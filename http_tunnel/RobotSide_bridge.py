import requests
import json
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

# Configuration
TUNNEL_URL = "http://127.0.0.1:8000"

class TunnelBridge(Node):
    def __init__(self):
        super().__init__('tunnel_bridge')
        # Create a publisher for a topic called 'radio_data'
        self.publisher_ = self.create_publisher(String, 'radio_data', 10)
        self.get_logger().info('Tunnel-to-ROS Bridge Started')

    def publish_to_ros(self, data):
        msg = String()
        # Convert dictionary to JSON string to publish
        msg.data = json.dumps(data)
        self.publisher_.publish(msg)
        self.get_logger().info(f'Published to ROS: {msg.data}')

def send_and_bridge(bridge, endpoint, data):
    try:
        url = f"{TUNNEL_URL.rstrip('/')}/{endpoint.lstrip('/')}"
        response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            # Parse/Strip the response and publish it
            bridge.publish_to_ros(result)
            return result
            
    except Exception as e:
        print(f"Bridge Error: {e}")

if __name__ == "__main__":
    rclpy.init() #ROS 2 Python client
    bridge_node = TunnelBridge()
    
    # Example
    my_payload = {"sensor": "temp", "value": 22.5}
    send_and_bridge(bridge_node, "/robot/telemetry", my_payload)
    
    # Keep node alive briefly to ensure publishing completes
    rclpy.shutdown()