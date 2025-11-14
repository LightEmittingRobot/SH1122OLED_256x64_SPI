# sh1122.py - stable-ish driver

from machine import Pin, SPI
import time

class SH1122:
    WIDTH  = 256
    HEIGHT = 64

    def __init__(self, spi, dc, cs, rst,
                 col_offset=0,
                 row_offset=0,
                 a0_cmd=0x14): 

        self.spi = spi
        self.dc  = dc
        self.cs  = cs
        self.rst = rst

        self.col_offset = col_offset
        self.row_offset = row_offset
        self.a0_cmd     = a0_cmd

        self.dc.init(Pin.OUT, value=0)
        self.cs.init(Pin.OUT, value=1)
        self.rst.init(Pin.OUT, value=1)

        # 4-bit grayscale framebuffer (2 pixels/byte)
        self.buffer = bytearray((self.WIDTH * self.HEIGHT) // 2)

        self.reset()
        self.init_display()

    def reset(self):
        self.rst.value(0)
        time.sleep_ms(20)
        self.rst.value(1)
        time.sleep_ms(20)

    def _cmd(self, *cmd):
        self.dc.value(0)
        self.cs.value(0)
        self.spi.write(bytearray(cmd))
        self.cs.value(1)

    def _data(self, buf):
        self.dc.value(1)
        self.cs.value(0)
        self.spi.write(buf)
        self.cs.value(1)

    # ------------------------
    #   REVERTED INIT
    # ------------------------
    def init_display(self):

        self._cmd(0xAE)          # Display OFF
        self._cmd(0x2F)          # internal power
        self._cmd(0xA4)          # display follows RAM
        self._cmd(0xA6)          # normal mode
        self._cmd(0xAD, 0x80)    # internal regulator

        self._cmd(0x81, 0x80)    # Contrast mid
        self._cmd(0x20, 0x81)    # Gray scale mode

        # *** Critical mapping commands ***
        self._cmd(0xA0)          # SEG remap normal
        self._cmd(0xC0)          # COM scan normal
        self._cmd(0x40 | 0x00)   # Start line = 0

        # *** Known-good addressing windows ***
        # 256px → 128 nibbles → 0..0x7F
        self._cmd(0x15, 0x00, 0x7F)  # Column start/end
        self._cmd(0x75, 0x00, 0x3F)  # Row start/end (0..63)

        self._cmd(0xAF)          # Display ON

    # ------------------------
    # Pixel / drawing
    # ------------------------
    def contrast(self, level):
        self._cmd(0x81, max(0, min(255, level)))

    def fill(self, gray):
        g = (max(0, min(15, gray)) & 0x0F)
        b = (g << 4) | g
        self.buffer[:] = bytes([b]) * len(self.buffer)

    def pixel(self, x, y, gray):
        if not (0 <= x < self.WIDTH and 0 <= y < self.HEIGHT):
            return
        g = max(0, min(15, gray)) & 0x0F
        idx = y * (self.WIDTH // 2) + (x // 2)
        old = self.buffer[idx]
        if x & 1:
            self.buffer[idx] = (old & 0xF0) | g
        else:
            self.buffer[idx] = (g << 4) | (old & 0x0F)

    def hline(self, x, y, w, gray):
        for i in range(w):
            self.pixel(x+i, y, gray)

    def vline(self, x, y, h, gray):
        for i in range(h):
            self.pixel(x, y+i, gray)

    def rect(self, x, y, w, h, gray):
        self.hline(x, y, w, gray)
        self.hline(x, y+h-1, w, gray)
        self.vline(x, y, h, gray)
        self.vline(x+w-1, y, h, gray)

    # ------------------------
    #   DISPLAY REFRESH
    # ------------------------
    def show(self):
        bytes_per_row = self.WIDTH // 2

        for y in range(self.HEIGHT):
            panel_row = (y + self.row_offset) & 0x3F

            self._cmd(0x75, panel_row, 0x3F)  # row addr
            self._cmd(0x15, 0x00, 0x7F)       # col addr

            start = y * bytes_per_row
            end   = start + bytes_per_row
            self._data(memoryview(self.buffer)[start:end])
