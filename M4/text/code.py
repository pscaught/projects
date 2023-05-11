"""Test code to retrieve data from a json payload and display it as text"""

import gc
import board
import busio
import random
import terminalio
import time
from digitalio import DigitalInOut
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
from adafruit_esp32spi import adafruit_esp32spi
import adafruit_requests as requests
#print('adafruit_requests', gc.mem_free())
from adafruit_matrixportal.matrix import Matrix
matrix = Matrix()
#from adafruit_matrixportal.network import Network
from adafruit_display_text.scrolling_label import ScrollingLabel
from adafruit_bitmap_font.bitmap_font import load_font

#import adafruit_requests

# WiFi


# Test of simpler approach, but it seems to not have retry logic
# and may have a memory issue
#network = Network(status_neopixel=board.NEOPIXEL, debug=False)
#network.connect()
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
    except ConnectionError as e:
        print("could not connect to AP, retrying: ", e)
        continue
print("Connected to", str(esp.ssid, "utf-8"), "\tRSSI:", esp.rssi)

# Initialize a requests object with a socket and esp32spi interface
socket.set_interface(esp)
requests.set_socket(socket, esp)


display = matrix.display

#font = terminalio.FONT
font = load_font("/IBMPlexMono-Medium-24_jep.bdf")
blue = 0x0000FF
green = 0x00FF00
red = 0xFF0000
color = blue

text = "testing 1 2 3 4 5 6 "
color = red
#text_area = label.Label(font, text=text, color=color)
#display.show(text_area)

#gc.collect()

#def update_text(text, x=10, color=red):
#    text_area = Label(font, text=text, color=color)
#
#    text_area.x = x
#    text_area.y = 15
#
#    text_area.color = color
#    gc.collect()
#    display.show(text_area)

#i = 20
text_area = ScrollingLabel(font, text=text, color=color, max_characters=5)
text_area.y = 15
text_area.scale = 1
#text_area.anchor_point = (1.0, 0.5)
#text_area.anchored_position = (0,0)
text_area.padding_top = 20
display.show(text_area)
while True:
    text_area.update()
#    text_length = len(text)
#    print(gc.mem_free())
#    print(text_length)
#    try:
#        update_text(text, i, color)
#    except MemoryError as e:
#        print("Some error occured, retrying! -", e)
#        text = text[:-1]
#        gc.collect()
#    if text_length < 64:
#        text_offset = text_length * 6
#    else:
#        text_offset = 64 * 6
#    i -= 1
#    if i < 20 - (text_offset):
#        color = [red, green, blue][random.randint(0, 2)]
#        i = 20
#        #text = network.fetch_data("http://192.168.10.10:8000/data.json", json_path=["text"])
#        r = requests.get("http://192.168.10.10:8000/data.json")
#        text = r.json()['text']
#        gc.collect()
#    time.sleep(0.05)
