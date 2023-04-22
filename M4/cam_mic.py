from adafruit_matrixportal.matrix import Matrix  # first import to prevent crash

matrix = Matrix()
import adafruit_display_text.label
import time
import board
import displayio
import vectorio
from adafruit_display_shapes.circle import Circle
from adafruit_display_shapes.rect import Rect
from adafruit_display_shapes.roundrect import RoundRect

# from adafruit_display_shapes.polygon import Polygon
from adafruit_bitmap_font import bitmap_font
from adafruit_matrixportal.network import Network
from displayio import Palette

display = matrix.display
network = Network(status_neopixel=board.NEOPIXEL, debug=False)
# --- Drawing setup ---
# Create a Group
group = displayio.Group()
# Create a bitmap object
bitmap = displayio.Bitmap(64, 32, 2)  # width, height, bit depth
# Create a color palette
color = displayio.Palette(4)
color[0] = 0x000000  # black
color[1] = 0xFF0000  # red
color[2] = 0x444444  # dim white
color[3] = 0xDD8000  # gold
# Create a TileGrid using the Bitmap and Palette
tile_grid = displayio.TileGrid(bitmap, pixel_shader=color)
# Add the TileGrid to the Group
group.append(tile_grid)


def draw_cam():
    cam_body = RoundRect(10, 10, 21, 12, 2, fill=color[2], outline=color[2], stroke=1)
    group.append(cam_body)
    # display.show(group)
    time.sleep(0)

    cam_top1 = RoundRect(17, 7, 7, 3, 2, fill=color[2], outline=color[2], stroke=1)
    group.append(cam_top1)
    # display.show(group)
    time.sleep(0)

    cam_top2 = RoundRect(16, 8, 9, 2, 2, fill=color[2], outline=color[2], stroke=1)
    group.append(cam_top2)
    # display.show(group)
    time.sleep(0)

    # palette = Palette(1)
    # palette[0] = color[0]

    # circle = vectorio.Circle(pixel_shader=palette, radius=4, x=20, y=15)
    cam_lens = Circle(20, 15, 4, fill=color[0])
    group.append(cam_lens)
    # display.show(group)
    time.sleep(0)


def draw_mic():
    mic_body = RoundRect(44, 7, 5, 10, 2, fill=color[2], outline=color[2], stroke=1)
    group.append(mic_body)

    mic_base_left1 = Rect(42, 15, 1, 2, fill=color[2])
    group.append(mic_base_left1)

    mic_base_left2 = Rect(43, 17, 1, 1, fill=color[2])
    group.append(mic_base_left2)

    mic_base_top = Rect(44, 18, 5, 1, fill=color[2])
    group.append(mic_base_top)

    mic_base_right1 = Rect(50, 15, 1, 2, fill=color[2])
    group.append(mic_base_right1)

    mic_base_right2 = Rect(49, 17, 1, 1, fill=color[2])
    group.append(mic_base_right2)

    mic_base_bottom = Rect(46, 18, 1, 4, fill=color[2])
    group.append(mic_base_bottom)


def cam_mute():
    # Just dumb enough to work
    for i in range(19):
        dot = Rect(29 - i, 6 + i, 1, 1, fill=color[1])
        group.append(dot)


def mic_mute():
    for i in range(16):
        dot = Rect(53 - i, 7 + i, 1, 1, fill=color[1])
        group.append(dot)


if __name__ == "__main__":
    draw_cam()
    draw_mic()
    display.show(group)

    cam_mute()
    time.sleep(10)
    print("Waiting for the cam to mute")

    mic_mute()
    time.sleep(10)
    print("Waiting for the mic to mute")
    display.show(group)

    while True:
        time.sleep(10000)
