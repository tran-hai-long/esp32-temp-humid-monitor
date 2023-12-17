from _thread import start_new_thread
from dht import DHT22
from json import dumps
from i2c_lcd import I2cLcd
from lcd_api import LcdApi
from machine import Pin, SoftI2C
from socket import socket, AF_INET, SOCK_STREAM
from time import sleep
from umqtt.simple import MQTTClient


# Set up variables
prev_temp = 1
new_temp = 1
prev_humid = 0
new_humid = 0
# track temp and humid changes
update = False
# Initiate DHT22
dht22 = DHT22(Pin(32))
# Initiate LCD
# i2c = SoftI2C(scl=Pin(22), sda=Pin(21), freq=10000)
# lcd = I2cLcd(i2c, 0x27, 2, 16)


# Read DHT22 sensor values
def read_dht22():
    dht22.measure()
    temp = dht22.temperature()
    humid = dht22.humidity()
    return (temp, humid)


# Print string to LCD
# def print_lcd(string):
#     lcd.clear()
#     lcd.putstr(string)


def send_data_socket():
    sock = socket(AF_INET, SOCK_STREAM)
    server_ip = "192.168.92.91"
    server_port = 9999
    sock.connect((server_ip, server_port))
    while True:
        # send sensor data to the server
        if update:
            data = {"temp": new_temp, "humid": new_humid}
            data_json = dumps(data)
            sock.send(data_json.encode("utf-8"))
            update = False
            sleep(2)


# Update sensors in an interval
def update_sensors():
    global prev_temp, new_temp, prev_humid, new_humid, update
    while True:
        prev_temp = new_temp
        prev_humid = new_humid
        try:
            new_temp, new_humid = read_dht22()
        except:
            print("Can not read DHT22")
        if new_temp != prev_temp or new_humid != prev_humid:
            update = True
            # start_new_thread(print_lcd, (f"{new_temp}'C\n{new_humid} %",))
        sleep(3)


# Method for sending sensor data to MQTT server regularly
def send_data_mqtt():
    mqtt_server = "broker.hivemq.com"
    client = MQTTClient("group7_dht22_pub", mqtt_server, port=1883)
    client.connect()
    while True:
        sleep(10)
        try:
            client.publish(b"iot_group7_temp", bytes(str(new_temp), "utf-8"))
            client.publish(b"iot_group7_humid", bytes(str(new_humid), "utf-8"))
        except:
            print("Can not send data to MQTT server")


# Initiate threads
start_new_thread(update_sensors, ())
start_new_thread(send_data_socket, ())
start_new_thread(send_data_mqtt, ())
