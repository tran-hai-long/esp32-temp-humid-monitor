from _thread import start_new_thread
from microWebSrv import MicroWebSrv
from time import sleep
from json import dumps, loads
from socket import socket, AF_INET, SOCK_STREAM

# Set up variables
prev_temp = 1
new_temp = 1
prev_humid = 0
new_humid = 0
max_temp = 40
max_humid = 50


def receive_data_socket():
    global prev_temp, new_temp, prev_humid, new_humid
    sock = socket(AF_INET, SOCK_STREAM)
    server_ip = "192.168.92.91"
    port = 9999
    sock.bind((server_ip, port))
    sock.listen(0)
    print(f"Listening on {server_ip}:{port}")
    # accept incoming connections
    client_socket, client_address = sock.accept()
    print(f"Accepted connection from {client_address[0]}:{client_address[1]}")
    # receive data from the client
    while True:
        request = client_socket.recv(256)
        request = request.decode("utf-8")
        data = loads(request)
        prev_temp = new_temp
        prev_humid = new_humid
        new_temp = data["temp"]
        new_humid = data["humid"]


# websocket methods
def _accept_websocket_callback(websocket, httpClient):
    print("WebSocket accepted")
    websocket.RecvTextCallback = _recv_text_callback
    websocket.RecvBinaryCallback = _recv_binary_callback
    websocket.ClosedCallback = _closed_callback

    # Send temperature and humidity data to web visitors
    def send_dht_data():
        while True:
            if new_temp != prev_temp or new_humid != prev_humid:
                data = {"temp": new_temp, "humid": new_humid}
                websocket.SendText(dumps(data))
                sleep(2)

    send_dht_data()


# Receive command from web visitors
def _recv_text_callback(websocket, message):
    print(f"WebSocket received text: {message}")


def _recv_binary_callback(websocket, data):
    print(f"WebSocket received data: {data}")


def _closed_callback(websocket):
    print("WebSocket closed")


# Initiate threads
start_new_thread(receive_data_socket, ())
# Initiate web server
# TCP port 80 and files in /www
mws = MicroWebSrv(webPath="/www")
mws.MaxWebSocketRecvLen = 256
mws.AcceptWebSocketCallback = _accept_websocket_callback
mws.Start(threaded=True)
