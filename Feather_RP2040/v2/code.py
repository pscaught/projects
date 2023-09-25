import asyncio
import audiocore
import audiomixer
import digitalio
import board
import neopixel
import supervisor
import time
from audiopwmio import PWMAudioOut as AudioOut
from adafruit_seesaw.seesaw import Seesaw
from adafruit_seesaw.digitalio import DigitalIO
from adafruit_seesaw.pwmout import PWMOut

# disable auto-reload
supervisor.disable_autoreload()

# wait a little bit so USB can stabilize and not glitch audio
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

# list of (samples to play, mixer gain level)
wav_files = (
    #('wav/Twilight_Guitar1-MP3.wav', 1.0),
    #('wav/Twilight_Guitar2-MP3.wav', 1.0),
    #('wav/Twilight_Guitar3-MP3.wav', 1.0),
    #('wav/Twilight_Guitar4-MP3.wav', 1.0),
    #('wav/amen_22k16b_160bpm.wav', 1.0),
    ('wav/dnb21580_22k16b_160bpm.wav', 0.9),
    ('wav/drumloopA_22k16b_160bpm.wav', 1.0),
    #('wav/scratch3667_4bar_22k16b_160bpm.wav', 0.5),
    ('wav/femvoc_330662_half_22k16b_160bpm_01.wav', 0.8),
    #('wav/pt_limor_modem_vox_01.wav', 0.4),
    ('wav/snowpeaks_22k_s16.wav', 0.8),
    #('wav/dnb21580_22k16b_160bpm_rev.wav', 1.0)
)

audio = AudioOut(board.TX)  # RP2040 PWM, use RC filter on breadboard
mixer = audiomixer.Mixer(voice_count=len(wav_files), sample_rate=22050, channel_count=1,
                         bits_per_sample=16, samples_signed=True)
audio.play(mixer) # attach mixer to audio playback

for i in range(len(wav_files)):  # start all samples at once for use w handle_mixer
    wave = audiocore.WaveFile(open(wav_files[i][0], "rb"))
    mixer.voice[i].play(wave, loop=True)
    mixer.voice[i].level = 0

def handle_mixer(num, pressed):
    voice = mixer.voice[num]   # get mixer voice
    if pressed:
        voice.level = wav_files[num][1]  # play at level in wav_file list
        print(wav_files[num][0])
    else: # released
        voice.level = 0  # mute it

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

# Arcade buttons
arcade_qt = Seesaw(board.I2C(), addr=0x3A)

for d, _ in enumerate(data):
    button_pin = data[d]["button_pin"]
    button = DigitalIO(arcade_qt, button_pin)
    button.direction = digitalio.Direction.INPUT
    button.pull = digitalio.Pull.UP
    data[d]["button"] = button

    button_led_pin = data[d]["button_led_pin"]
    button_led = PWMOut(arcade_qt, button_led_pin)
    #button_led = DigitalIO(arcade_qt, button_led_pin)
    #button_led.direction = digitalio.Direction.OUTPUT
    data[d]["button_led"] = button_led

async def play(index):
    while True:
        if not data[index]['button'].value:
            color = data[index]['color']['rgb']
            feather_neopixel.fill(color)
            feather_led.value = True

            handle_mixer(index, True)
            for i in list(range(0, num_pixels))[index::4]:
                pixels[i] = color

            #data[index]['button_led'].value = True
            for cycle in range(0, 30000, 5000):
                data[index]['button_led'].duty_cycle = cycle
                await asyncio.sleep(0.01)
            for cycle in range(30000, 0, -5000):
                data[index]['button_led'].duty_cycle = cycle
                await asyncio.sleep(0.01)
            data[index]['button_led'].duty_cycle = 0
        else:
            #data[index]['button_led'].value = False
            #data[index]['button_led'].duty_cycle = 0
            handle_mixer(index, False)
            feather_led.value = False
            for i in list(range(0, num_pixels))[index::4]:
                pixels[i] = (0, 0, 0)

        await asyncio.sleep(0)

async def main():
    tasks = []
    tasks.append(asyncio.create_task(play(0)))
    tasks.append(asyncio.create_task(play(1)))
    tasks.append(asyncio.create_task(play(2)))
    tasks.append(asyncio.create_task(play(3)))
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(main())

