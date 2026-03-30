from .tunnel import make_app, make_lora_node
from .config import RADIO_PORT, FORWARD_TO_URL, TUNNEL_PORT, TUNNEL_IP

import uvicorn


app = make_app(FORWARD_TO_URL, make_lora_node(RADIO_PORT))

if __name__ == "__main__":
    uvicorn.run("__main__:app", host=TUNNEL_IP, port=TUNNEL_PORT, log_level="info")