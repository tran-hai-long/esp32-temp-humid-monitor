from _thread import start_new_thread
from dht import DHT22
from i2c_lcd import I2cLcd
from lcd_api import LcdApi
from machine import PWM, Pin, SoftI2C
from microWebSrv import MicroWebSrv
from time import sleep
from umqtt.simple import MQTTClient
import json
import network

# Set up variables
prev_temp = 1
new_temp = 1
prev_humid = 0
new_humid = 0
max_temp = 40
max_humid = 50
# Initiate DHT22
dht22 = DHT22(Pin(32))
# Initiate LCD
i2c = SoftI2C(scl=Pin(22), sda=Pin(21), freq=10000)
lcd = I2cLcd(i2c, 0x27, 2, 16)
# Initiate buzzer
# buzzer = PWM(Pin(4))
# Initiate RGB LED bulbs
led_temp = [PWM(Pin(26)), PWM(Pin(25)), PWM(Pin(33))]
led_humid = [PWM(Pin(12)), PWM(Pin(14)), PWM(Pin(27))]


# Read DHT22 sensor values
def read_dht22():
    dht22.measure()
    temp = dht22.temperature()
    humid = dht22.humidity()
    return (temp, humid)


# Print string to LCD
def print_lcd(string):
    lcd.clear()
    lcd.putstr(string)


# Control LED bulbs
def set_led_color(led, red, green, blue):
    led[0].duty_u16(int(red))
    led[1].duty_u16(int(green))
    led[2].duty_u16(int(blue))


# # Make buzzer play a tone
# def play_tone(frequency):
#     buzzer.duty_u16(1000)
#     buzzer.freq(frequency)


# # Stop buzzer
# def be_quiet():
#     buzzer.duty_u16(0)


# Update sensors in an interval
def update_sensors():
    global prev_temp, new_temp, prev_humid, new_humid
    while True:
        prev_temp = new_temp
        prev_humid = new_humid
        new_temp, new_humid = read_dht22()
        if new_temp != prev_temp or new_humid != prev_humid:
            start_new_thread(print_lcd, (f"{new_temp}'C\n{new_humid} %", ))
        # if new_temp > max_temp and new_humid > max_humid:
        #     play_tone(1000)
        # elif new_temp > max_temp:
        #     play_tone(700)
        # elif new_humid > max_humid:
        #     play_tone(400)
        # else:
        #     be_quiet()
        temp_percentage = new_temp / max_temp
        humid_percentage = new_humid / max_humid
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
        sleep(3)


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
    mqtt_server = "broker.hivemq.com";
    client = MQTTClient("group7_dht22_pub", mqtt_server, port=1883)
    client.connect()
    while True:
        sleep(10)
        client.publish(b"iot_group7_temp", bytes(str(new_temp), 'utf-8'))
        client.publish(b"iot_group7_humid", bytes(str(new_humid), 'utf-8'))


# Initiate threads
# be_quiet()
start_new_thread(update_sensors, ())
start_new_thread(send_data_mqtt, ())
# Initiate web server
# TCP port 80 and files in /www
mws = MicroWebSrv(webPath="/www")
mws.AcceptWebSocketCallback = _accept_websocket_callback
mws.Start(threaded=True)
