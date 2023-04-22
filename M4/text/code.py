"""Test code to retrieve data from a json payload and display it as text"""


import board
import busio
import random
import terminalio
import time

from digitalio import DigitalInOut
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
from adafruit_esp32spi import adafruit_esp32spi
import adafruit_requests as requests

from adafruit_matrixportal.matrix import Matrix
from adafruit_display_text import label

# WiFi

try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)

spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)

print("Connecting to AP...")
while not esp.is_connected:
    try:
        esp.connect_AP(secrets["ssid"], secrets["password"])
    except RuntimeError as e:
        print("could not connect to AP, retrying: ", e)
        continue
print("Connected to", str(esp.ssid, "utf-8"), "\tRSSI:", esp.rssi)

# Initialize a requests object with a socket and esp32spi interface
socket.set_interface(esp)
requests.set_socket(socket, esp)

matrix = Matrix()

display = matrix.display

font = terminalio.FONT
blue = 0x0000FF
green = 0x00FF00
red = 0xFF0000
color = blue

def update_text(text, x=10, color=red):
    text_area = label.Label(font, text=text, color=color)

    text_area.x = x
    text_area.y = 15

    text_area.color = color
    display.show(text_area)

    return (len(text) * 5)


i = 0
text = 'money money money'
color = red
while True:
    text_length = update_text(text, i, color)
    i -= 1
    if i < 0 - (text_length + 20):
        color = [red, green, blue][random.randint(0,2)]
        i = text_length
        r = requests.get('http://192.168.10.10:8000/data.json')
        text = r.json()['some']
    time.sleep(0.05)
