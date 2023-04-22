import random
import terminalio
import time
from adafruit_matrixportal.matrix import Matrix
from adafruit_display_text import label
matrix = Matrix()

display = matrix.display

text = 'That\'s a bomb!!!'

font = terminalio.FONT
blue = 0x0000FF
green = 0x00FF00
red = 0xFF0000
color = blue

text_area = label.Label(font, text=text, color=color)

text_area.x = 10
text_area.y = 15

display.show(text_area)

text_length = (len(text) * 5)
i = 0
while True:
    text_area.x = i
    i -= 1
    if i < 0 - (text_length + 20):
        i = text_length
        text_area.color = [red, green, blue][random.randint(0,2)]
    time.sleep(0.05)