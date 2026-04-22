# ── Config (edit per side) ────────────────────────────────────────────────────

# ======== RADIO SETTINGS ========
# The serial port of the LoRa module. Check your system's device manager to find the correct port.
RADIO_PORT         = "COM4"
# The maximum number of times the LoRa module will retransmit a message if no acknowledgement is received.
RETRIES            = 3
# The timeout between (re)transmissions over the radio channel in seconds.
RETRANSMIT_TIMEOUT = 2.0

# ======== TUNNEL SETTINGS ========
# Local IP to bind the tunnel server to.
TUNNEL_IP          = "localhost" 
# The port on which the tunnel will listen for incoming HTTP requests.
TUNNEL_PORT        = 8000

# ======== FORWARDING SETTINGS ========
# The URL to which the tunnel will forward incoming HTTP requests. This should be the address of the server you want to expose over LoRa.
FORWARD_TO_URL     = "http://your-server.com"
