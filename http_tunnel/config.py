# ── Config (edit per side) ────────────────────────────────────────────────────

# ======== RADIO SETTINGS ========
# The serial port of the LoRa module. Check your system's device manager to find the correct port.
# Or visit https://www.pyserial.org/docs/getting-started#find-your-device for help finding it.
RADIO_PORT         = "COM5"

# ======== TUNNEL SETTINGS ========
# The port on which the tunnel will listen on this device for incoming HTTP requests.
TUNNEL_PORT        = 8000

# ======== FORWARDING SETTINGS ========
# The URL to which the tunnel will forward incoming HTTP requests. This should be the address of the server you want to expose over LoRa.
FORWARD_TO_URL     = "http://localhost:3000"
