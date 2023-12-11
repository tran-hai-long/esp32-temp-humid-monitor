# This file is executed on every boot (including wake-boot from deepsleep)
# import esp
# esp.osdebug(None)
# import webrepl
# webrepl.start()

import network
import sys

# Add /lib-custom to module import list
sys.path.append("/lib-custom")

# Connect to Wi-Fi upon startup
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
if not wlan.isconnected():
    print("connecting to network...")
    wlan.connect("wifi-name", "password")
    while not wlan.isconnected():
        pass
print("network config:", wlan.ifconfig())
