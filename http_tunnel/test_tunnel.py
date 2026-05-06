"""
test_tunnel.py - Full local integration test for the radio HTTP tunnel
======================================================================
Runs all four components in one process, no LoRa hardware required.

lora-p2p's LoRaNode() (no port argument) creates a mock node that
communicates over a shared in-process MockMedium — so two mock nodes
automatically form a radio channel without any extra wiring.

    Robot (requests)
        |
        | HTTP  port 8000
        v
    Tunnel Side A  ---[mock LoRa medium]---  Tunnel Side B
                                                  |
                                                  | HTTP  port 8002
                                                  v
                                              Server (FastAPI)  port 8001

Usage:
    pip install fastapi uvicorn requests lora-p2p
    python test_tunnel.py
"""

import time
import threading
import logging

import requests
import uvicorn
from fastapi import FastAPI, Request

from .tunnel import make_app, make_lora_node

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

PORT_TUNNEL_A = 8000   # Robot talks to this  (fake Server API)
PORT_TUNNEL_B = 8002   # Server talks to this (fake Robot API)
PORT_SERVER   = 8001   # Real server


LARGE_TEST_JSON = {
        "users": [
            {
                "id": 1,
                "name": "John Doe",
                "email": "john@example.com",
                "is_active": True,
                "age": 30,
                "preferences": {
                    "theme": "dark",
                    "notifications": False
                }
            },
            {
                "id": 2,
                "name": "Jane Smith",
                "email": "jane@example.com",
                "is_active": False,
                "age": 25,
                "preferences": {
                    "theme": "light",
                    "notifications": True
                }
            },
            {
                "id": 3,
                "name": "Rick Sanchez",
                "email": "rick@example.com",
                "is_active": True,
                "age": 78,
                "preferences": {
                    "theme": "light",
                    "notifications": True
                }
            }
        ],
        "total_users": 3,
        "version": "1.0.0"
    }

# ── Fake Server ───────────────────────────────────────────────────────────────

def make_server_app() -> FastAPI:
    server = FastAPI(title="Real Server")

    @server.get("/status")
    async def status():
        return {"status": "ok", "message": "Server is up"}

    @server.post("/robot/errors")
    async def robot_errors(request: Request):
        body = await request.json()
        log.info(f"[server] Received error report: {body}")
        return {"received": True, "errors": body.get("errors", [])}

    @server.post("/robot/telemetry")
    async def robot_telemetry(request: Request):
        body = await request.json()
        return {"received": True, "data_points": len(body.get("readings", []))}

    @server.get("/robot/command")
    async def robot_command():
        return {"command": "move_forward", "speed": 1.5}
    
    @server.get("/large_json")
    async def large_json():
        return LARGE_TEST_JSON

    return server


# ── Server runner ─────────────────────────────────────────────────────────────

def run_server(app: FastAPI, port: int, label: str):
    cfg = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    srv = uvicorn.Server(cfg)
    threading.Thread(target=srv.run, name=label, daemon=True).start()
    for _ in range(50):
        try:
            requests.get(f"http://127.0.0.1:{port}/", timeout=5.0)
        except requests.exceptions.ConnectionError:
            time.sleep(0.1)
            continue
        break
    log.info(f"[{label}] listening on port {port}")


# ── Tests ─────────────────────────────────────────────────────────────────────

def run_tests():
    results = []

    def test(name, fn):
        try:
            fn()
            log.info(f"  ✓  {name}")
            results.append((name, True))
        except Exception as e:
            log.error(f"  ✗  {name}  →  {e}")
            results.append((name, False))

    base_a = f"http://127.0.0.1:{PORT_TUNNEL_A}"
    time_out_per_req = None

    def t_get_status():
        r = requests.get(f"{base_a}/status", timeout=time_out_per_req)
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def t_post_errors():
        payload = {"errors": ["sensor_fault", "low_battery"]}
        r = requests.post(f"{base_a}/robot/errors", json=payload, timeout=time_out_per_req)
        assert r.status_code == 200
        body = r.json()
        assert body["received"] is True
        assert "sensor_fault" in body["errors"]

    def t_post_telemetry():
        r = requests.post(f"{base_a}/robot/telemetry", json={"readings": [1.1, 2.2, 3.3]}, timeout=time_out_per_req)
        assert r.status_code == 200
        assert r.json()["data_points"] == 3

    def t_query_string():
        r = requests.get(f"{base_a}/status?verbose=true", timeout=time_out_per_req)
        assert r.status_code == 200

    def t_unknown_route():
        r = requests.get(f"{base_a}/does/not/exist", timeout=time_out_per_req)
        assert r.status_code == 404

    def t_get_connectivity():
        r = requests.get(f"{base_a}/connectivity", timeout=time_out_per_req)
        assert r.status_code == 200
        assert r.json().keys() == {"rssis", "snrs", "times"}
    
    def t_large_json():
        r = requests.get(f"{base_a}/large_json", timeout=time_out_per_req)
        assert r.json() == LARGE_TEST_JSON
    
    test("GET  /status                 (Robot → Server)", t_get_status)
    test("POST /robot/errors           (Robot → Server)", t_post_errors)
    test("POST /robot/telemetry        (Robot → Server)", t_post_telemetry)
    test("GET  /status?verbose=true    (query string passthrough)", t_query_string)
    test("GET  /does/not/exist         (404 passthrough)", t_unknown_route)
    test("GET  /connectivity           (Robot → Server)", t_get_connectivity)
    test("GET /large_json              (Robot → Server)", t_large_json)


    passed = sum(1 for _, ok in results if ok)
    total  = len(results)
    print(f"\n{'='*50}")
    print(f"  {passed}/{total} tests passed")
    print(f"{'='*50}\n")
    return passed == total


# ── Main ──────────────────────────────────────────────────────────────────────

def test():
    print("\n=== Radio HTTP Tunnel - Local Integration Test ===\n")

    # Two mock LoRa nodes — no port means mock, they share a MockMedium automatically
    tunnel_a = make_app(forward_to_url=f"http://127.0.0.1:{PORT_SERVER}", node=make_lora_node("COM4"))
    tunnel_b = make_app(forward_to_url=f"http://127.0.0.1:{PORT_SERVER}", node=make_lora_node("COM5"))
    server   = make_server_app()

    run_server(server,   PORT_SERVER,   "Server  ")
    run_server(tunnel_a, PORT_TUNNEL_A, "Tunnel-A")
    run_server(tunnel_b, PORT_TUNNEL_B, "Tunnel-B")

    print("\n--- Running tests ---\n")
    success = run_tests()
    raise SystemExit(0 if success else 1)