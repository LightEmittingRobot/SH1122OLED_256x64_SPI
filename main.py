from machine import SPI, Pin
from utime import sleep
from sh1122 import SH1122

spi = SPI(0, baudrate=8_000_000, polarity=0, phase=0,
          sck=Pin(18), mosi=Pin(19), miso=Pin(16))

oled = SH1122(
    spi,
    dc=Pin(20),
    cs=Pin(17),
    rst=Pin(21),
    row_offset=0,   # adjust ONLY this for vertical shift
    col_offset=0,
)

# ---- Test patterns ----

def pattern_checker():
    oled.fill(0)
    for y in range(oled.HEIGHT):
        for x in range(oled.WIDTH):
            if ((x // 8) ^ (y // 8)) & 1:
                oled.pixel(x, y, 15)
    oled.show()

def pattern_crosshair():
    oled.fill(0)
    oled.rect(0, 0, oled.WIDTH, oled.HEIGHT, 15)
    oled.hline(0, oled.HEIGHT // 2, oled.WIDTH, 15)
    oled.vline(oled.WIDTH // 2, 0, oled.HEIGHT, 15)
    oled.show()

def pattern_white():
    oled.fill(15)
    oled.show()

def pattern_black():
    oled.fill(0)
    oled.show()

patterns = [
    ("White", pattern_white),
    ("Black", pattern_black),
    ("Crosshair", pattern_crosshair),
    ("Checker", pattern_checker),
]

while True:
    for name, f in patterns:
        print("Showing:", name)
        f()
        sleep(3)