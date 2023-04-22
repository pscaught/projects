from adafruit_matrixportal.matrix import Matrix
matrix = Matrix()
import time
import board
import displayio
import adafruit_display_text.label
from adafruit_display_shapes.rect import Rect
from adafruit_display_shapes.polygon import Polygon
from adafruit_bitmap_font import bitmap_font
from adafruit_matrixportal.network import Network
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
rect1 = Rect(0, 0, 2, 32, fill=color[2])
group.append(rect1)
display.show(group)
rect1 = Rect(0, 10, 2, 32, fill=color[2])
display.show(group)
group.append(rect1)
display.show(group)
rect1 = Rect(0, 0, 3, 32, fill=color[2])
group.append(rect1)
display.show(group)
rect1 = Rect(0, 0, 1, 32, fill=color[2])
group.append(rect1)
display.show(group)
rect1 = Rect(0, 0, 4, 32, fill=color[2])
display.show(group)
group.append(rect1)
rect1 = Rect(0, 0, 4, 32, fill=color[0])
group.append(rect1)
rect1 = Rect(10, 10, 30, 15, fill=color[2])
group.append(rect1)
rect1 = Rect(10, 10, 30, 15, fill=color[1])
group.append(rect1)
rect1 = Rect(10, 10, 30, 15, fill=color[3])
group.append(rect1)
rect1 = Rect(10, 10, 30, 15, fill=color[4])
group.append(rect1)
rect1 = Rect(10, 10, 30, 15, fill=color[0])
group.append(rect1)
rect1 = Rect(10, 10, 30, 15, fill=color[1])
group.append(rect1)
rect1 = Rect(10, 10, 30, 15, fill=color[2])
group.append(rect1)
rect2 = Rect(15, 7, 15, 3, fill=color[2])
group.append(rect2)
rect2 = Rect(15, 7, 15, 3, fill=color[0])
group.append(rect2)
rect2 = Rect(20, 7, 15, 3, fill=color[0])
group.append(rect2)
rect2 = Rect(15, 7, 15, 3, fill=color[0])
rect2 = Rect(20, 7, 15, 3, fill=color[2])
group.append(rect2)
rect2 = Rect(20, 7, 15, 3, fill=color[0])
group.append(rect2)
rect2 = Rect(18, 7, 15, 3, fill=color[0])
rect2 = Rect(18, 7, 15, 3, fill=color[2])
group.append(rect2)
rect2 = Rect(18, 7, 15, 3, fill=color[0])
group.append(rect2)
rect2 = Rect(17, 7, 15, 3, fill=color[2])
group.append(rect2)
rect2 = Rect(17, 7, 15, 3, fill=color[0])
group.append(rect2)
rect2 = Rect(19, 7, 15, 3, fill=color[2])
group.append(rect2)
rect2 = Rect(18, 7, 14, 3, fill=color[2])
group.append(rect2)
rect2 = Rect(18, 7, 14, 3, fill=color[0])
group.append(rect2)
rect2 = Rect(18, 7, 16, 3, fill=color[0])
group.append(rect2)
rect2 = Rect(18, 7, 14, 3, fill=color[2])
group.append(rect2)
rect2 = Rect(18, 7, 16, 3, fill=color[2])
group.append(rect2)
rect2 = Rect(17, 7, 16, 3, fill=color[2])
rect2 = Rect(18, 7, 16, 3, fill=color[0])
rect2 = Rect(18, 7, 17, 3, fill=color[0])
group.append(rect2)
rect2 = Rect(17, 7, 16, 3, fill=color[2])
group.append(rect2)
bitmap_file = open('camera.bmp', 'rb')
bitmap = displayio.OnDiskBitmap(bitmap_file)
from displayio import Palette
palette = Palette()
palette = Palette(1)
import vectorio
palette[0] = 0x125690
circle = vectorio.Circle(pixel_shader=pallete, radius=25, x=20, y=20)
circle = vectorio.Circle(pixel_shader=palette, radius=25, x=20, y=20)
group.append(circle)
circle = vectorio.Circle(pixel_shader=palette, radius=4, x=20, y=20)
group.append(circle)
circle = vectorio.Circle(pixel_shader=palette, radius=4, x=20, y=20)