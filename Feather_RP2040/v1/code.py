import audiopwmio
import audiocore
import audiomixer
import audiomp3
import board
#import busio
import digitalio
import terminalio
import displayio
import neopixel
import time

from adafruit_seesaw.seesaw import Seesaw
from adafruit_seesaw.digitalio import DigitalIO

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
decode = audiomp3.MP3Decoder(open('Twilight_Guitar1-MP3.mp3', 'rb'))
#decode = audiocore.WaveFile(open('full_ring.wav', 'rb'))

mixer = audiomixer.Mixer(
        voice_count=1,
        sample_rate=22050,
        channel_count=1,
        bits_per_sample=16,
        samples_signed=True
)
audio.play(mixer)
mixer.voice[0].level = 1.0

# display


data = [
    {
        'color': {'rgb': (255, 0, 0), 'name': 'red'},
        'button_pin': 18,
        'button_led_pin': 12,
    },
    {
        'color': {'rgb': (255, 255, 0), 'name': 'yellow'},
        'button_pin': 19,
        'button_led_pin': 13,
    },
    {
        'color': {'rgb': (0, 255, 0), 'name': 'green'},
        'button_pin': 20,
        'button_led_pin': 0,
    },
    {
        'color': {'rgb': (255, 255, 255), 'name': 'white'},
        'button_pin': 2,
        'button_led_pin': 1,
    }
]

# for Feather RP2040
#i2c = busio.I2C(board.SCL, board.SDA)
arcade_qt = Seesaw(board.I2C(), addr=0x3A)

for d, _ in enumerate(data):
    button_pin = data[d]['button_pin']
    button = DigitalIO(arcade_qt, button_pin)
    button.direction = digitalio.Direction.INPUT
    button.pull = digitalio.Pull.UP
    data[d]['button'] = button

    button_led_pin = data[d]['button_led_pin']
    button_led = DigitalIO(arcade_qt, button_led_pin)
    button_led.direction = digitalio.Direction.OUTPUT
    data[d]['button_led'] = button_led


while True:
    for i, _ in enumerate(data):
        trigger = not data[i]['button'].value
        color = data[i]['color']['rgb']
        _button_led = data[i]['button_led']
        if trigger:
            print(data[i]['color']['name'])
            _button_led.value = True
            feather_neopixel.fill(color)
            feather_led.value = True
            #audio.play(decode)
            mixer.voice[0].level = 1.0
            mixer.voice[0].play(decode, loop=True)
            color_seq(pixels, color, num_pixels)
            _button_led.value = False
            mixer.voice[0].stop()
        else:
            feather_led.value = False

