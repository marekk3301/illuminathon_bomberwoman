import rotaryio
import board
import time
import random
from digitalio import DigitalInOut, Direction, Pull
import math
import usb_cdc
import neopixel
import analogio

encoder_x = rotaryio.IncrementalEncoder(board.GP17, board.GP16)
encoder_y = rotaryio.IncrementalEncoder(board.GP14, board.GP15)
last_position = (None, None)

btn_x = DigitalInOut(board.GP18)
btn_x.direction = Direction.INPUT
btn_x.pull = Pull.UP
btn_y = DigitalInOut(board.GP13)
btn_y.direction = Direction.INPUT
btn_y.pull = Pull.UP

pixel_pin = board.GP2
num_pixels = 3
pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=0.5, auto_write=False)

ring_pin = board.GP3
num_ring_pixels = 12
ring_pixels = neopixel.NeoPixel(ring_pin, num_ring_pixels, brightness=0.5, auto_write=False)


pixels.fill((0, 0, 0))
pixels.show()

pin_10 = DigitalInOut(board.GP10)
pin_10.direction = Direction.OUTPUT

pin_11 = DigitalInOut(board.GP11)
pin_11.direction = Direction.OUTPUT

pin_12 = DigitalInOut(board.GP12)
pin_12.direction = Direction.OUTPUT


pin_19 = DigitalInOut(board.GP19)
pin_19.direction = Direction.INPUT
pin_19.pull = Pull.UP

pin_20 = DigitalInOut(board.GP20)
pin_20.direction = Direction.INPUT
pin_20.pull = Pull.UP

pin_21 = DigitalInOut(board.GP21)
pin_21.direction = Direction.INPUT
pin_21.pull = Pull.UP

colors_to_pin = {pin_10: (200, 100, 0), # Y
                pin_11: (150, 0, 100), # P
                pin_12: (0, 50, 150)} # B

pins = [pin_10, pin_11, pin_12]
shuffled_pins = []

disarmed = False
is_disarming = False


def generateBomb():
    bomb_x = random.randint(0, 63)
    bomb_y = random.randint(0, 31)
    if usb_cdc.data:
        message = f"BOMB:{bomb_x},{bomb_y}\n"
        usb_cdc.data.write(message.encode())
    return bomb_x, bomb_y


def radians_to_bomb(X, Y, W, Z):
    # Obliczenie kąta theta w stronę miny (W, Z)
    theta = math.atan2(Z - Y, W - X)
    theta_degrees = math.degrees(theta)
    
    return theta_degrees


def theta_in_range(x):
    ranges = {(-105, -75): 0,
              (-75, -45): 1, 
              (-45, -15): 2,
              (-15, 15): 3,
              (15, 45): 4,
              (45, 75): 5,
              (75, 105): 6,
              (105, 135): 7,
              (135, 165): 8,
              #(-165, 165): 9, # we fricking dumb lol
              (-180, -165): 9,
              (165, 180): 9,
              (-165, -135): 10,
              (-135, -105): 11 }
    for low, high in ranges:
        if low <= x < high:
            return ranges[(low, high)]
            

def prepare_bomb():
    disarmed_pin_1 = False
    disarmed_pin_2 = False
    disarmed_pin_3 = False
    # TODO non repeating shuffles
    while pins:
        index = random.randint(0, len(pins) - 1)
        shuffled_pins.append(pins.pop(index))
    return shuffled_pins


shuffled_pins = prepare_bomb()

def is_position_next_to_bomb(point, center_x, center_y, side_length=5):
    half_side = (side_length - 1) / 2
    x, y = point
    return (center_x - half_side <= x <= center_x + half_side) \
        and (center_y - half_side <= y <= center_y + half_side)


bomb_x, bomb_y = generateBomb()
near_bomb_start_time = None
near_bomb_duration = 15 
timer_active = False
previous_time = -1

while True:
    if encoder_x.position < 0:
        encoder_x.position = encoder_x.position + 1
    elif encoder_x.position >= 64:
        encoder_x.position = encoder_x.position - 1
        
    if encoder_y.position < 0:
        encoder_y.position = encoder_y.position + 1
    elif encoder_y.position >= 32:
        encoder_y.position = encoder_y.position - 1
    position = (encoder_x.position,
                encoder_y.position)

    if (position[0] == bomb_x and position[1] == bomb_y):
        print("KABOOM")    
        if usb_cdc.data:
            message = f"KAA"
            usb_cdc.data.write(message.encode())
        break
    elif is_position_next_to_bomb(position, bomb_x, bomb_y):
        ring_pixels.fill((150, 0, 0)) 
        ring_pixels.show()
        
        if not timer_active:
            near_bomb_start_time = time.monotonic()
            timer_active = True
        # timer start
    else:
        theta = radians_to_bomb(bomb_x, bomb_y, position[0], position[1])
        part = theta_in_range(theta)
        # print(part)    
        ring_pixels.fill((0, 50, 0))
        ring_pixels[part] = (200, 0, 0)
        ring_pixels.show()

    if timer_active:
        if previous_time != int(time.monotonic() - near_bomb_start_time):
            print(int(time.monotonic() - near_bomb_start_time))
            previous_time = int((time.monotonic() - near_bomb_start_time))
            
        if time.monotonic() - near_bomb_start_time >= near_bomb_duration:
            print("Time's up! KABOOM")
            if usb_cdc.data:
                message = f"KAA"
                usb_cdc.data.write(message.encode())
            break

        pixels[0] = colors_to_pin[shuffled_pins[0]]
        pixels.show()
        shuffled_pins[0].value = False
        shuffled_pins[1].value = True
        shuffled_pins[2].value = True
        if not pin_19.value:
            pixels[1] = colors_to_pin[shuffled_pins[1]]
            pixels.show()
            shuffled_pins[0].value = True
            shuffled_pins[1].value = False
            shuffled_pins[2].value = True
            if not pin_20.value:
                pixels[2] = colors_to_pin[shuffled_pins[2]]
                pixels.show()
                shuffled_pins[0].value = True
                shuffled_pins[1].value = True
                shuffled_pins[2].value = False
                if not pin_21.value:
                    if usb_cdc.data:
                        message = f"WIN"
                        usb_cdc.data.write(message.encode())
                    break

    if usb_cdc.data:
        if position != last_position:
            message = f"POS:{position[0]},{position[1]}\n"
            usb_cdc.data.write(message.encode())
            last_position = position

        if not btn_x.value:
            is_disarming = True

        if not btn_y.value:
            usb_cdc.data.write(b"Y_BUTTON_DOWN\n")
            print("button")
                    
    time.sleep(0.1)
