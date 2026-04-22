"""
Radio HTTP Tunnel - Symmetric HTTP-over-radio bridge
=====================================================
Run the same script on both sides of the radio link, with different config.

Dependencies: fastapi, uvicorn, requests, lora-p2p
Run with: uvicorn tunnel:app --host 0.0.0.0 --port 8000
"""

import json
import asyncio
import logging
import requests

from fastapi import FastAPI, Request, Response
from lora_p2p import LoRaNode, ReliableCommunicatingNode
from .config import RETRIES, RETRANSMIT_TIMEOUT

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


def make_lora_node(port: str | None = None) -> LoRaNode:
    """
    Returns a LoRaNode for the given port.
    If port is None, returns a mock node (no hardware required).
    """
    return LoRaNode(port=port)


# ── Serialization helpers ─────────────────────────────────────────────────────

def serialize_request(method: str, path: str, headers: dict, body: bytes) -> bytes:
    return json.dumps({
        "method":  method,
        "path":    path,
        "headers": dict(headers),
        "body":    body.decode(errors="replace"),
    }).encode()

def deserialize_request(data: bytes) -> dict:
    return json.loads(data.decode())

def serialize_response(status_code: int, headers: dict, body: bytes) -> bytes:
    skip = {"transfer-encoding", "content-encoding", "connection"}
    return json.dumps({
        "status":  status_code,
        "headers": {k: v for k, v in headers.items() if k.lower() not in skip},
        "body":    body.decode(errors="replace"),
    }).encode()

def deserialize_response(data: bytes) -> dict:
    return json.loads(data.decode())


# ── App factory ───────────────────────────────────────────────────────────────
# Factory function so multiple tunnel instances can be created in one process
# (used in tests). The production entry point at the bottom calls this once.

def make_app(forward_to_url: str, node: LoRaNode) -> FastAPI:
    """
    Create a tunnel app.

    Args:
        forward_to_url: Base URL to forward inbound radio requests to.
        node:           A LoRaNode instance (real or mock). make_app() wraps it
                        in a ReliableCommunicatingNode internally.
    """

    def on_radio_request(message_data: tuple) -> bytes:
        raw = message_data[0]
        log.info(f"Received radio request ({len(raw)} bytes)")
        try:
            req  = deserialize_request(raw)
            url  = forward_to_url.rstrip("/") + req["path"]
            log.info(f"Forwarding {req['method']} {url}")
            resp = requests.request(
                method=req["method"], url=url,
                headers=req["headers"], data=req["body"].encode(),
                timeout=10, allow_redirects=False,
            )
            log.info(f"Got response: HTTP {resp.status_code}")
            return serialize_response(resp.status_code, dict(resp.headers), resp.content)
        except Exception as e:
            log.error(f"Failed to forward request: {e}")
            return json.dumps({"status": 502, "headers": {}, "body": f"Tunnel error: {e}"}).encode()

    radio = ReliableCommunicatingNode(node, on_radio_request)
    app   = FastAPI(title="Radio HTTP Tunnel")

    # =============== OPTIONAL: Connectivity monitoring endpoint ===============
    # Store latest connectivity measurements (for monitoring/debugging)
    rssi: int | None = None
    snr:  int | None = None

    @app.api_route("/connectivity", methods=["GET"])
    async def connectivity():
        """Endpoint to get connectivity measurements (rssi, snr) of the radio"""
        return {"rssi": rssi, "snr": snr}
    
    # ==============================================================================

    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
    async def tunnel_request(path: str, request: Request):
        body      = await request.body()
        full_path = "/" + path
        if request.url.query:
            full_path += "?" + request.url.query

        log.info(f"Tunnelling {request.method} {full_path} over radio")
        skip    = {"host", "content-length", "transfer-encoding", "connection"}
        #headers = {k: v for k, v in request.headers.items() if k.lower() not in skip}
        headers = {}
        packet  = serialize_request(request.method, full_path, headers, body)
        """
        # DEBUG
        for k, v in headers.items():
            print(f"  {k}: {v}")
        """
        try:
            answer_data = await asyncio.to_thread(
                radio.send_reliably_wait_for_answer, packet,
                max_retries=RETRIES, retransmission_timeout=RETRANSMIT_TIMEOUT,
            )
            resp = deserialize_response(answer_data[0])

            # =============== Update connectivity measurements ===============
            connectivity_measurements = answer_data[1]
            global rssi, snr
            rssi = connectivity_measurements.rssi
            snr  = connectivity_measurements.snr
            # ==============================================================================

            log.info(f"Returning HTTP {resp['status']} to caller")
            return Response(content=resp["body"].encode(), status_code=resp["status"], headers=resp["headers"])
        except TimeoutError:
            log.warning("No response from other side over radio")
            return Response(content="Radio timeout", status_code=504)
        except Exception as e:
            log.error(f"Tunnel error: {e}")
            return Response(content=f"Tunnel error: {e}", status_code=502)

    return app
