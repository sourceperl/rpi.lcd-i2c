# -*- coding: utf-8 -*-
"""
Compiled, mashed and generally mutilated 2014-2015 by Denis Pleic
Made available under GNU GENERAL PUBLIC LICENSE

# Modified Python I2C library for Raspberry Pi
# as found on http://www.recantha.co.uk/blog/?p=4849
# Joined existing 'i2c_lib.py' and 'lcddriver.py' into a single library
# added bits and pieces from various sources
# By DenisFromHR (Denis Pleic)
# 2015-02-10, ver 0.1
# Modified by sourceperl (Loïc Lefebvre)
# 2016-02-15
"""
import smbus
from time import *

# some const
# LCD Address
LCD_ADDRESS = 0x27

# commands
LCD_CLEARDISPLAY = 0x01
LCD_RETURNHOME = 0x02
LCD_ENTRYMODESET = 0x04
LCD_DISPLAYCONTROL = 0x08
LCD_CURSORSHIFT = 0x10
LCD_FUNCTIONSET = 0x20
LCD_SETCGRAMADDR = 0x40
LCD_SETDDRAMADDR = 0x80

# flags for display entry mode
LCD_ENTRYRIGHT = 0x00
LCD_ENTRYLEFT = 0x02
LCD_ENTRYSHIFTINCREMENT = 0x01
LCD_ENTRYSHIFTDECREMENT = 0x00

# flags for display on/off control
LCD_DISPLAYON = 0x04
LCD_DISPLAYOFF = 0x00
LCD_CURSORON = 0x02
LCD_CURSOROFF = 0x00
LCD_BLINKON = 0x01
LCD_BLINKOFF = 0x00

# flags for display/cursor shift
LCD_DISPLAYMOVE = 0x08
LCD_CURSORMOVE = 0x00
LCD_MOVERIGHT = 0x04
LCD_MOVELEFT = 0x00

# flags for function set
LCD_8BITMODE = 0x10
LCD_4BITMODE = 0x00
LCD_2LINE = 0x08
LCD_1LINE = 0x00
LCD_5x10DOTS = 0x04
LCD_5x8DOTS = 0x00

# offset for up to 4 rows
LCD_ROW_OFFSET = (0x80, 0xC0, 0x94, 0xD4)

# flags for backlight control
LCD_BACKLIGHT = 0x08
LCD_NOBACKLIGHT = 0x00

En = 0b00000100  # Enable bit
Rw = 0b00000010  # Read/Write bit
Rs = 0b00000001  # Register select bit


class I2cDevice:
    def __init__(self, addr, port=1):
        self.addr = addr
        self.bus = smbus.SMBus(port)

    # Write a single command
    def write_cmd(self, cmd):
        self.bus.write_byte(self.addr, cmd)
        sleep(0.0001)

    # Write a command and argument
    def write_cmd_arg(self, cmd, data):
        self.bus.write_byte_data(self.addr, cmd, data)
        sleep(0.0001)

    # Write a block of data
    def write_block_data(self, cmd, data):
        self.bus.write_block_data(self.addr, cmd, data)
        sleep(0.0001)

    # Read a single byte
    def read(self):
        return self.bus.read_byte(self.addr)

    # Read
    def read_data(self, cmd):
        return self.bus.read_byte_data(self.addr, cmd)

    # Read a block of data
    def read_block_data(self, cmd):
        return self.bus.read_block_data(self.addr, cmd)


class LCD:
    def __init__(self, i2c_addr=LCD_ADDRESS):
        """
        Init LCD class and panel

        :param i2c_addr: i2c address
        :type i2c_addr: int
        """
        # private vars
        self._back_light = False
        self._lcd_device = I2cDevice(i2c_addr)
        # init display
        self.write_cmd(0x03)
        self.write_cmd(0x03)
        self.write_cmd(0x03)
        self.write_cmd(0x02)
        self.write_cmd(LCD_FUNCTIONSET | LCD_2LINE | LCD_5x8DOTS | LCD_4BITMODE)
        self.write_cmd(LCD_DISPLAYCONTROL | LCD_DISPLAYON)
        self.write_cmd(LCD_CLEARDISPLAY)
        self.write_cmd(LCD_ENTRYMODESET | LCD_ENTRYLEFT)
        sleep(.2)

    def _strobe(self, data):
        """
        Clocks En pin to latch current command

        :param data:
        :return:
        """
        # set back light
        data |= LCD_BACKLIGHT if self._back_light else LCD_NOBACKLIGHT
        # clock data with a pulse on En pin
        self._lcd_device.write_cmd(data | En)
        sleep(.0005)
        self._lcd_device.write_cmd(data & ~En)
        sleep(.0001)

    def write_cmd(self, cmd):
        """
        Write a command to LCD panel

        :param cmd: value of command byte
        :type cmd: int
        """
        self._strobe(cmd & 0xF0)
        self._strobe((cmd << 4) & 0xF0)

    def write_char(self, char_value):
        """
        Write a char to LCD panel or character ROM

        :param char_value: value of char
        :type char_value: int
        """
        self._strobe(Rs | (char_value & 0xF0))
        self._strobe(Rs | ((char_value << 4) & 0xF0))

    def message(self, string):
        """
        Send string to LCD panel to display it

        :param string: string to display
        :type string: str
        """
        for char in string:
            self.write_char(ord(char))

    def home(self):
        """
        Home the cursor

        """
        self.write_cmd(LCD_RETURNHOME)

    def clear(self):
        """
        Clear LCD and home cursor

        """
        self.write_cmd(LCD_CLEARDISPLAY)
        self.write_cmd(LCD_RETURNHOME)

    def set_cursor(self, col=0, row=0):
        """
        Move cursor to col, row

        :param col: column id (default is 0)
        :type col: int
        :param row: row id (default is 0)
        :type row: int
        """
        # set max row
        if row > 3:
            row = 3
        # set location
        self.write_cmd(LCD_SETDDRAMADDR | (col + LCD_ROW_OFFSET[row]))

    def set_backlight(self, state):
        """
        Define back light state

        :param state: back light status to set
        :type state: bool
        """
        self._back_light = bool(state)
        self._lcd_device.write_cmd(LCD_BACKLIGHT if self._back_light else LCD_NOBACKLIGHT)

    def load_custom_chars(self, font_data):
        """
        Add custom chars (8 max)

        :param font_data:
        :type font_data: array
        """
        # set CGRAM mode
        self.write_cmd(LCD_SETCGRAMADDR)
        # transfer data to CGRAM
        for char in font_data:
            for line in char:
                self.write_char(line)
