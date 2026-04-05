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

1) Install the dependencies.

2) change the `config.py` file with the correct values for your setup.

3) Run the application on the command line using
    ```cmd
    $ python -m http_tunnel
    ```
4) Now you can send http messages to one of the tunnel sides, which will be passed on over the LoRa medium and then handled by the server on the other side. The answer of the server will travel back over the LoRa medium and arrive at the original sender.
