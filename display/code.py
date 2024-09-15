import time
import board
import displayio
import framebufferio
import rgbmatrix
import random
import usb_cdc

displayio.release_displays()

matrix = rgbmatrix.RGBMatrix(
    width=64, height=32, bit_depth=3,
    rgb_pins=[board.R0, board.G0, board.B0, board.R1, board.G1, board.B1],
    addr_pins=[board.ROW_A, board.ROW_B, board.ROW_C, board.ROW_D],
    clock_pin=board.CLK, latch_pin=board.LAT, output_enable_pin=board.OE
)

display = framebufferio.FramebufferDisplay(matrix, auto_refresh=False)

SCALE = 1
bitmap = displayio.Bitmap(display.width // SCALE, display.height // SCALE, 8)
palette = displayio.Palette(8)
tilegrid = displayio.TileGrid(bitmap, pixel_shader=palette)

group = displayio.Group(scale=SCALE)
group.append(tilegrid)

display.root_group = group

palette[0] = 0x000020  # Black
palette[1] = 0xFFFFFF  # White
palette[2] = 0xFF0000  # Red 
palette[3] = 0x000000  # Off
palette[4] = 0x7FFFFF  # inner
palette[5] = 0xF0F000  # middle
palette[6] = 0xFD0000  # outer

coords = [0, 0]
bomb_x, bomb_y = [0, 0]

display.auto_refresh = True

def parse_serial_input(data):
    """Parses incoming serial data and returns a tuple with x, y coordinates."""
    try:
        x_str, y_str = data.strip().split(",")
        return int(x_str), int(y_str)
    except ValueError:
        return None


def clear_and_boom(bitmap, display, X, Y):
    for i in range(display.width):
        for j in range(display.height):
            bitmap[i, j] = 3

    max_radius = 10 

    # Draw eplosion 
    for r in range(max_radius, 0, -1):
        color = 0 

        if r > 6:
            color = 6  # Red
        elif r > 4:
            color = 5  # Yellow
        else:
            color = 4  # Dark green

        for dx in range(-r, r+1):
            for dy in range(-r, r+1):
                if 0 <= X + dx < display.width and 0 <= Y + dy < display.height:
                    distance_squared = dx*dx + dy*dy
                    if distance_squared <= r*r:
                        bitmap[X + dx, Y + dy] = color


i = 0

while True:
    if usb_cdc.data:
      if usb_cdc.data.in_waiting > 0:
            serial_data = usb_cdc.data.readline().decode().strip()
            
            if "KAA" in serial_data:
                clear_and_boom(bitmap, display, bomb_x, bomb_y)
                break
            if "POS:" in serial_data:  # "x,y" in message
                coords = parse_serial_input(serial_data[4:])
                if coords:
                    x, y = coords
                    
                    # clear bitmap
                    for i in range(display.width):
                        for j in range(display.height):
                            bitmap[i, j] = 0
                    
                    if 0 <= x < display.width and 0 <= y < display.height:
                        for i in range(display.width):
                            bitmap[i, y] = 1
                        for i in range(display.height):
                            bitmap[x, i] = 1
            elif "BOMB:" in serial_data:
                coords = parse_serial_input(serial_data[5:])
                if coords:
                    bomb_x, bomb_y = coords

            elif "X_BUTTON_DOWN" in serial_data:
                print("X button pressed")

            elif "Y_BUTTON_DOWN" in serial_data:
                print("Y button pressed")

            elif "Y_BUTTON_DOWN" in serial_data:
                print("Y button pressed")
            
            bitmap[bomb_x, bomb_y] = 2
    
    display.refresh()
    time.sleep(0.05)
