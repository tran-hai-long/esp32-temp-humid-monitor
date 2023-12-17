from _thread import start_new_thread
from json import dumps, loads
from machine import PWM, Pin
from microWebSrv import MicroWebSrv
from socket import socket, AF_INET, SOCK_STREAM
from time import sleep

# Set up variables
temp = 1
humid = 0
min_temp = 0
max_temp = 40
min_humid = 0
max_humid = 50
# variable to track min max changes (sent from web visitors)
update = False
# Initiate buzzer
# buzzer = PWM(Pin(4))
# Initiate RGB LED bulbs
# led_temp = [PWM(Pin(26)), PWM(Pin(25)), PWM(Pin(33))]
# led_humid = [PWM(Pin(12)), PWM(Pin(14)), PWM(Pin(27))]


# Control LED bulbs
# def set_led_color(led, red, green, blue):
#     led[0].duty_u16(int(red))
#     led[1].duty_u16(int(green))
#     led[2].duty_u16(int(blue))


# Make buzzer play a tone
# def play_tone(frequency):
#     buzzer.duty_u16(1000)
#     buzzer.freq(frequency)


# Stop buzzer
# def be_quiet():
#     buzzer.duty_u16(0)


# Receive sensor data from slave ESP32
def receive_data_socket():
    global temp, humid, update
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
        temp = data["temp"]
        humid = data["humid"]
        update = True


# Update sensors in an interval
def update_sensors():
    while True:
        if (temp > max_temp or temp < min_temp) and (
            humid > max_humid or humid < min_humid
        ):
            play_tone(1000)
        elif temp > max_temp or temp < min_temp:
            play_tone(700)
        elif humid > max_humid or humid < min_humid:
            play_tone(400)
        else:
            be_quiet()
        temp_percentage = temp / max_temp
        humid_percentage = humid / max_humid
        # clamp led color values in (0, 65535) range
        set_led_color(
            led_temp,
            max(min(65535 * temp_percentage, 65535), 0),
            max(min(65535 * (1 - temp_percentage), 65535), 0),
            0,
        )
        set_led_color(
            led_humid,
            0,
            max(min(65535 * (1 - humid_percentage), 65535), 0),
            max(min(65535 * humid_percentage, 65535), 0),
        )
        sleep(2)


# Websocket methods
def _accept_websocket_callback(websocket, httpClient):
    print("WebSocket accepted")
    websocket.RecvTextCallback = _recv_text_callback
    websocket.ClosedCallback = _closed_callback

    # Send temperature and humidity data to web visitors
    def send_dht_data():
        global update
        while True:
            if update:
                data = {
                    "temp": temp,
                    "humid": humid,
                    "min_temp": min_temp,
                    "max_temp": max_temp,
                    "min_humid": min_humid,
                    "max_humid": max_humid,
                }
                websocket.SendText(dumps(data))
                update = False
                sleep(2)

    start_new_thread(send_dht_data, ())


# Receive command from web visitors
def _recv_text_callback(websocket, message):
    global min_temp, max_temp, min_humid, max_humid
    print(f"WebSocket message: {message}")
    client_message = loads(message)
    if "min_temp" in client_message:
        min_temp = float(client_message["min_temp"])
        update_min_max = True
    if "max_temp" in client_message:
        max_temp = float(client_message["max_temp"])
        update_min_max = True
    if "min_humid" in client_message:
        min_humid = float(client_message["min_humid"])
        update_min_max = True
    if "max_humid" in client_message:
        max_humid = float(client_message["max_humid"])
        update_min_max = True


def _closed_callback(websocket):
    print("WebSocket closed")


# Initiate threads
start_new_thread(receive_data_socket, ())
start_new_thread(update_sensors, ())
# Initiate web server, TCP port 80 and files in /www
mws = MicroWebSrv(webPath="/www")
mws.MaxWebSocketRecvLen = 256
mws.AcceptWebSocketCallback = _accept_websocket_callback
mws.Start(threaded=True)
