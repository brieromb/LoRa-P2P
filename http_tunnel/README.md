# Radio HTTP Tunnel - Symmetric HTTP-over-radio bridge
An application made on top of the lora-p2p module in this repository.

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
This application uses only the following external python dependencies:

`fastapi`, `uvicorn`, `requests`

## How to setup
The following steps are to set up a single side of the tunnel.
A functional tunnel has 2 sides that are set up in this way.

0) Clone this repository (and create a virtual environment and activate it)

1) Install the dependencies using 
```cmd
pip install fastapi uvicorn requests
```

2) change the `config.py` file with the correct values for the setup of this tunnel side.

3) Run the application on the command line using
    ```cmd
    $ python -m http_tunnel
    ```
4) Now you can send http messages to the tunnel sides, which will be passed on over the LoRa medium and then handled by the entity on the other side. The answer of the entity to this http request will travel back over the LoRa medium and arrive at the original sender.

# Connectivity endpoint
This tunnel application also provides a `/connectivity` endpoint. This is not strictly necessary for the functionality of the `http_tunnel`, so it can be omitted.

This endpoint returns the SNR and RSSI measurements of the radio communication up till the present time. This can be used for debugging or to display the connection quality over time.

It can be expanded upon to for example show the connectivity measurements over time, so that it can be plotted.
