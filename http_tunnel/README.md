# Radio HTTP Tunnel - Symmetric HTTP-over-radio bridge

Run the same script on both sides of the radio link, with different config. This allows two server instances to communicate with each other over a radio link, using regular HTTP requests.

    Server A
        ^
        |
        | HTTP 
        |
        v
    Tunnel Side A  ---[LoRa medium]---  Tunnel Side B
                                                  ^
                                                  |
                                             HTTP |
                                                  |
                                                  v
                                              Server B

## Dependencies
This application uses only the following python modules:

`fastapi`, `uvicorn`, `requests`, `lora-p2p`

These can all be installed using `pip install`

## How to setup
The following steps are to set up a single side of the tunnel.
You need to go through the steps for both tunnel sides.

1) Install the dependencies.

2) change the `config.py` file with the correct values for the setup of this tunnel side.

3) Run the application on the command line using
    ```cmd
    $ python -m http_tunnel
    ```
4) Now you can send http messages to one of the tunnel sides, which will be passed on over the LoRa medium and then handled by the server on the other side. The answer of the server will travel back over the LoRa medium and arrive at the original sender.

# Connectivity endpoint
This tunnel application also provides a `/connectivity` endpoint. This is not strictly necessary for the functionality of the `http_tunnel`, so it can be omitted.

This endpoint returns the latest SNR and RSSI measurements of the radio communication. This can be used for debugging or to display the connection quality.

It can be expanded upon to for example show the connectivity measurements over time, so that it can be plotted.