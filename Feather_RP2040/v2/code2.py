import atexit
import audiopwmio
import audiocore
import audiomixer
import audiomp3
import board

# import busio
import digitalio
import terminalio
#import displayio
import neopixel
import time

#from adafruit_display_text import label
#from adafruit_ili9341 import ILI9341
from adafruit_seesaw.seesaw import Seesaw
from adafruit_seesaw.digitalio import DigitalIO

time.sleep(3)
# Neopixel on the Feather RP2040
feather_neopixel = neopixel.NeoPixel(board.NEOPIXEL, 1)
feather_neopixel.brightness = 0.01

# Onboard LED
feather_led = digitalio.DigitalInOut(board.LED)
feather_led.direction = digitalio.Direction.OUTPUT

# Neopixel strip
num_pixels = 19
pixels = neopixel.NeoPixel(board.D4, num_pixels, pixel_order=neopixel.RGB)
pixels.brightness = 0.3
pixels.fill((0, 0, 0))


def color_seq(_neopixel, _color, r):
    for i in range(r):
        _neopixel[i] = _color
        time.sleep(0.2)
    time.sleep(0.5)
    for i in range(r)[::-1]:
        _neopixel[i] = (0, 0, 0)
        time.sleep(0.1)


# audio
audio = audiopwmio.PWMAudioOut(board.TX)
decode = audiomp3.MP3Decoder(open("Twilight_Guitar1-MP3.mp3", "rb"))
# decode = audiocore.WaveFile(open('full_ring.wav', 'rb'))

mixer = audiomixer.Mixer(
    voice_count=1,
    sample_rate=22050,
    channel_count=1,
    bits_per_sample=16,
    samples_signed=True,
)
# audio.play(mixer)
mixer.voice[0].level = 0.0

# display
#displayio.release_displays()
#spi = board.SPI()
#tft_cs = board.D9
#tft_dc = board.D10
#
#display_bus = displayio.FourWire(
#    spi, command=tft_dc, chip_select=tft_cs, reset=board.D6
#)
#
#display = ILI9341(display_bus, width=320, height=240)
#text_group = displayio.Group()
#display.show(text_group)
#
#font = terminalio.FONT
#
#color_label = label.Label(font, scale=3, text="Hello", color=0x00FF00)
#
#color_label.x = 0
#color_label.y = 60
#
#text_group.append(color_label)

data = [
    {
        "color": {"rgb": (255, 0, 0), "name": "red", "hex": 0xFF0000},
        "button_pin": 18,
        "button_led_pin": 12,
    },
    {
        "color": {"rgb": (255, 255, 0), "name": "yellow", "hex": 0xFFFF00},
        "button_pin": 19,
        "button_led_pin": 13,
    },
    {
        "color": {"rgb": (0, 255, 0), "name": "green", "hex": 0x00FF00},
        "button_pin": 20,
        "button_led_pin": 0,
    },
    {
        "color": {"rgb": (255, 255, 255), "name": "white", "hex": 0xFFFFFF},
        "button_pin": 2,
        "button_led_pin": 1,
    },
]

# for Feather RP2040
# i2c = busio.I2C(board.SCL, board.SDA)
arcade_qt = Seesaw(board.I2C(), addr=0x3A)

for d, _ in enumerate(data):
    button_pin = data[d]["button_pin"]
    button = DigitalIO(arcade_qt, button_pin)
    button.direction = digitalio.Direction.INPUT
    button.pull = digitalio.Pull.UP
    data[d]["button"] = button

    button_led_pin = data[d]["button_led_pin"]
    button_led = DigitalIO(arcade_qt, button_led_pin)
    button_led.direction = digitalio.Direction.OUTPUT
    data[d]["button_led"] = button_led


audio.play(mixer)
mixer.voice[0].play(decode, loop=True)

while True:
    for i, _ in enumerate(data):
        #data[i]['button_led'].value = not data[i]["button"].value
        if not data[i]['button'].value:
            data[i]['button_led'].value = True

            mixer.voice[0].level = 1.0
            while not data[i]['button'].value:
                pass

            mixer.voice[0].level = 0.0
            data[i]['button_led'].value = False


        #color = data[i]["color"]["rgb"]
        #_button_led = data[i]["button_led"]
        #if trigger:
        #    # print(data[i]['color']['name'])
        #    #color_label.text = data[i]["color"]["name"]
        #    #color_label.color = data[i]["color"]["hex"]
        #    _button_led.value = True
        #    #feather_neopixel.fill(color)
        #    #feather_led.value = True
        #    mixer.voice[0].play(decode, loop=True)
        #    #color_seq(pixels, color, num_pixels)
        #    _button_led.value = False
        #else:
        #    mixer.voice[0].level = 0.0
        #    feather_led.value = False
