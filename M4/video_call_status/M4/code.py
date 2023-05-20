# SPDX-FileCopyrightText: 2020 John Park for Adafruit Industries
#
# SPDX-License-Identifier: MIT

# Video Call Status and Clock
# Runs on Airlift Metro M4 with 64x32 RGB Matrix display & shield

import adafruit_esp32spi.adafruit_esp32spi_socket as socket
import adafruit_requests as requests
import board
import busio
import displayio
import gc
import rtc
import time
from adafruit_display_shapes.circle import Circle
from adafruit_display_shapes.rect import Rect
from adafruit_display_shapes.roundrect import RoundRect
from adafruit_display_text.label import Label
from adafruit_esp32spi import adafruit_esp32spi
from adafruit_bitmap_font import bitmap_font
from adafruit_matrixportal.matrix import Matrix
from digitalio import DigitalInOut

AIO_URL = "https://io.adafruit.com/api/v2/%s/integrations/time/strftime?x-aio-key=%s&tz=%s&fmt=%s"
BLINK = True
DEBUG = False

# --- Network setup ---

# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise
print("    Video Call Status and Clock")
print("Time will be set for {}".format(secrets["timezone"]))

esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)

spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)


def connect():
    while not esp.is_connected:
        try:
            print("Connecting to AP...")
            esp.connect_AP(secrets["ssid"], secrets["password"])
        except ConnectionError as e:
            print("could not connect to AP, retrying: ", e)
            continue
        print("Connected to", str(esp.ssid, "utf-8"), "\tRSSI:", esp.rssi)
    else:
        return

# Initialize a requests object with a socket and esp32spi interface
socket.set_interface(esp)
requests.set_socket(socket, esp)


# --- Display setup ---
matrix = Matrix()
display = matrix.display

# --- Drawing setup ---
color = displayio.Palette(4)  # Create a color palette
color[0] = 0x000000  # black background
color[1] = 0xFF0000  # red
color[2] = 0x444444  # dim white
# color[2] = 0xCC4000  # amber
color[3] = 0x85FF00  # greenish


# BACKGROUND
background_group = displayio.Group()  # Create a Group
bitmap = displayio.Bitmap(64, 32, 2)  # Create a bitmap object,width, height, bit depth

# Create a TileGrid using the Bitmap and Palette
tile_grid = displayio.TileGrid(bitmap, pixel_shader=color)
background_group.append(tile_grid)  # index 0
display.show(background_group)

# DEVICES
#  Camera

# below is the result of trial and error creating a simple camera shape
device_group = displayio.Group()
cam_body = RoundRect(10, 10, 21, 12, 2, fill=color[2], outline=color[2], stroke=1)
cam_top1 = RoundRect(17, 7, 7, 3, 2, fill=color[2], outline=color[2], stroke=1)
cam_top2 = RoundRect(16, 8, 9, 2, 2, fill=color[2], outline=color[2], stroke=1)
cam_lens = Circle(20, 15, 4, fill=color[0])
device_group.append(cam_body)
device_group.append(cam_top1)
device_group.append(cam_top2)
device_group.append(cam_lens)

# Mic

# below is the result of trial and error creating a simple microphone shape
mic_body = RoundRect(44, 7, 5, 10, 2, fill=color[2], outline=color[2], stroke=1)
mic_base_left1 = Rect(42, 15, 1, 2, fill=color[2])
mic_base_left2 = Rect(43, 17, 1, 1, fill=color[2])
mic_base_top = Rect(44, 18, 5, 1, fill=color[2])
mic_base_right1 = Rect(50, 15, 1, 2, fill=color[2])
mic_base_right2 = Rect(49, 17, 1, 1, fill=color[2])
mic_base_bottom = Rect(46, 18, 1, 5, fill=color[2])
device_group.append(mic_body)
device_group.append(mic_base_left1)
device_group.append(mic_base_left2)
device_group.append(mic_base_top)
device_group.append(mic_base_right1)
device_group.append(mic_base_right2)
device_group.append(mic_base_bottom)
device_group.hidden = True  # Hide it initially

background_group.append(device_group)  # index 1

# Just dumb enough to work
# below we are using a for loop to create rectangles that are offset from
# each other in order to form a red slash through a camera
cam_mute_group = displayio.Group()
for i in range(17):
    dot = Rect(27 - i, 7 + i, 3, 1, fill=color[1])
    cam_mute_group.append(dot)

cam_mute_group.hidden = True
background_group.append(cam_mute_group)  # index 2


#gc.collect()
# same as the camera slash above
mic_mute_group = displayio.Group()
for i in range(16):
    dot = Rect(53 - i, 7 + i, 3, 1, fill=color[1])
    mic_mute_group.append(dot)

mic_mute_group.hidden = True
background_group.append(mic_mute_group)  # index 3


font_small = bitmap_font.load_font("/Teeny-Tiny-Pixls-5.bdf")
font_big = bitmap_font.load_font("/IBMPlexMono-Medium-24_jep.bdf")

clock_label_big = Label(font_big, padding_top=0, background_color=None)
clock_label_big.hidden = False  # this is all we show by default
clock_label_small = Label(font_small, padding_top=0, background_color=None)
clock_label_small.hidden = True
background_group.append(clock_label_big)  # index 4
background_group.append(clock_label_small)  # index 5

# --- Functions ---


def url_encode(url):
    return url.replace(" ", "+").replace("%", "%25").replace(":", "%3A")


def get_local_time():
    aio_url_formatted = AIO_URL % (
        secrets["aio_username"],
        secrets["aio_key"],
        url_encode(secrets["timezone"]),
        url_encode("%Y-%m-%d %H:%M:%S.%L %j %u %z %Z"),
    )
    connect()
    with requests.get(aio_url_formatted, timeout=10) as r:
        reply = r.text
        if reply:
            times = reply.split(" ")
            the_date = times[0]
            the_time = times[1]
            year_day = int(times[2])
            week_day = int(times[3])
            is_dst = None  # no way to know yet
            year, month, mday = [int(x) for x in the_date.split("-")]
            the_time = the_time.split(".")[0]
            hours, minutes, seconds = [int(x) for x in the_time.split(":")]
            now = time.struct_time(
                (year, month, mday, hours, minutes, seconds, week_day, year_day, is_dst)
            )
        r.close()

        if rtc is not None:
            rtc.RTC().datetime = now
    #gc.collect()

def get_data(server="192.168.10.10", port=8000):
    try:
        connect()
        print('getting data...', end='')
        with requests.get(f"http://{server}:{port}/data.json") as r:
            data = r.json()
            r.close()
        print('got data')
        #gc.collect()
        return data
    except Exception as e:
        #gc.collect()
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(e).__name__, e.args)
        print(message)
        return None



def update_time(*, hours=None, minutes=None, show_colon=False, small=False):
    now = time.localtime()  # Get the time values we need

    global BLINK

    # determine which clock size/font we're using
    if small:
        clock_label = clock_label_small
        clock_label.y = display.height - 3
        clock_label.font = bitmap_font.load_font("/Teeny-Tiny-Pixls-5.bdf")
    else:
        clock_label = clock_label_big
        clock_label.y = display.height // 2
        clock_label.font = bitmap_font.load_font("/IBMPlexMono-Medium-24_jep.bdf")

    if hours is None:
        hours = now[3]
    if hours >= 18 or hours < 6:  # evening hours to morning
        clock_label.color = color[1]
    else:
        clock_label.color = color[3]  # daylight hours
    if hours > 12:  # Handle times later than 12:59
        hours -= 12
    elif not hours:  # Handle times between 0:00 and 0:59
        hours = 12

    if minutes is None:
        minutes = now[4]

    if BLINK:
        # colon = ":" if show_colon or now[5] % 2 else " "
        colon = ":" if show_colon else " "
        BLINK = not BLINK
    else:
        colon = ":"
        BLINK = (
            not BLINK
        )  # TODO: this will currently always enable blink on the next pass

    clock_label.text = "{hours}{colon}{minutes:02d}".format(
        hours=hours, minutes=minutes, colon=colon
    )
    bbx, bby, bbwidth, bbh = clock_label.bounding_box
    # Center the label
    clock_label.x = round(display.width / 2 - bbwidth / 2)

    if DEBUG:
        print("Label bounding box: {},{},{},{}".format(bbx, bby, bbwidth, bbh))
        print("Label x: {} y: {}".format(clock_label.x, clock_label.y))


last_check_devices = None
last_check_time = None
update_time(show_colon=True)  # Display whatever time is on the board
server_active = False

while True:
    # hourly check
    if last_check_time is None or time.monotonic() > last_check_time + 1800:
        try:
            update_time(
                small=True, show_colon=True
            )  # Make sure a colon is displayed while updating
            get_local_time()  # Synchronize Board's clock to Internet
            last_check_time = time.monotonic()
            # print memory usage once an hour
            #print("current mem", gc.mem_free())
        except RuntimeError as e:
            print("Some error occured, retrying! -", e)

    # refresh device data from server every 10 seconds
    if last_check_devices is None or time.monotonic() > last_check_devices + 10:
        # decide which display layout to use depending on if we are getting
        # live data from the server
        # background_group[1] is devices
        # background_group[2] is camera mute slash
        # background_group[3] is mic mute slash
        # background_group[4] is big clock
        # background_group[5] is small clock
        # TODO: this is sometimes failing even when the server is running
        _data = get_data()
        if _data is not None:
            background_group[1].hidden = False
            background_group[2].hidden = (
                True if _data.get("camActive", False) else False
            )
            background_group[3].hidden = (
                True if _data.get("micActive", False) else False
            )
            background_group[4].hidden = True
            background_group[5].hidden = False
            server_active = True
            last_check_devices = time.monotonic()
        else:
            background_group[1].hidden = True
            background_group[2].hidden = True
            background_group[3].hidden = True
            background_group[4].hidden = False
            background_group[5].hidden = True
            server_active = False
            # check again in 20 seconds
            last_check_devices = time.monotonic() + 30
            #print("the server is not responding")
        #print("current free memory:", gc.mem_free())

    if server_active:
        update_time(small=True)
    else:
        update_time(small=False)

    # gc.collect()
    # print(gc.mem_free())
    #print('tick')
    time.sleep(1)
