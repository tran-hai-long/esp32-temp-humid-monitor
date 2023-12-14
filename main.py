from _thread import start_new_thread
from microWebSrv import MicroWebSrv
from time import sleep
from umqtt.simple import MQTTClient
import json

# Set up variables
prev_temp = 1
new_temp = 1
prev_humid = 0
new_humid = 0
max_temp = 40
max_humid = 50


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
                websocket.SendText(json.dumps(data))
                sleep(3)

    start_new_thread(send_dht_data, ())


# Receive command from web visitors
def _recv_text_callback(websocket, message):
    print(f"WebSocket received text: {message}")


def _recv_binary_callback(websocket, data):
    print(f"WebSocket received data: {data}")


def _closed_callback(websocket):
    print("WebSocket closed")


# Method for sending sensor data to MQTT server regularly
def send_data_mqtt():
    mqtt_server = "broker.hivemq.com"
    client = MQTTClient("group7_dht22_pub", mqtt_server, port=1883)
    client.connect()
    while True:
        sleep(10)
        client.publish(b"iot_group7_temp", bytes(str(new_temp), "utf-8"))
        client.publish(b"iot_group7_humid", bytes(str(new_humid), "utf-8"))


# Initiate threads
start_new_thread(send_data_mqtt, ())
# Initiate web server
# TCP port 80 and files in /www
mws = MicroWebSrv(webPath="/www")
mws.AcceptWebSocketCallback = _accept_websocket_callback
mws.Start(threaded=True)
