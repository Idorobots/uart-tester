#! /bin/env python3

import sys
import argparse
import time
from tester import Tester

# ICL7170:
# Data: I0-I7, O0-O7 via buffer
# Address: O8-O12
# /CS: O13
# /WR: O14
# /RD: O15
# /INT: I8
# INTS: GND
# ALE: 5V
# OSC IN: 4mhz crystal
# OSC OUT: 4mhz crystal

ZERO = b"00000000"
HIGHZ = b"ZZZZZZZZ"

SET = b'1'
UNSET = b'0'

tester = None

failures = 0

def test(actual, expected, info):
    global failures

    if actual != expected:
        failures = failures + 1
        print("Test failed: {}, {} != {}".format(info, expected, actual))

def read_inputs():
    raw = tester.read_inputs()
    value = {
        'data': raw[0:8],
        'interrupt': raw[8:9]
    }
    return value

def set_rtc(cs, wr, rd, addr, data):
    value = data & 0xff
    value = value | ((addr & 0xff) << 8)
    value = value | (cs << 13)
    value = value | (wr << 14)
    value = value | (rd << 15)
    tester.set_outputs(value)
    return read_inputs()

def write_reg(reg, data):
    set_rtc(1, 1, 1, reg, data)
    set_rtc(0, 0, 1, reg, data)
    set_rtc(1, 1, 1, reg, data)

def read_reg(reg):
    set_rtc(1, 1, 1, reg, 0x00)
    set_rtc(0, 1, 0, reg, 0x00)
    value = read_inputs()
    set_rtc(1, 1, 1, reg, 0x00)
    return value

def check_reg(reg, expected, interrupt, hint):
    value = read_reg(reg)
    test(value['data'], expected, hint + " - data")
    test(value['interrupt'], interrupt, hint + " - interrupt")
    return value

def bits(val):
    return bytes("{0:08b}".format(val & 0xff), 'latin1')

def test_rtc():
    # Initial sanity check
    set_rtc(1, 1, 1, 0x00, 0x00)
    init = read_inputs()
    test(init['data'], HIGHZ, "Data floating after startup")
    test(init['interrupt'], SET, "No interrupt after startup")

    # Reset interrupts
    write_reg(0x10, 0x00)
    check_reg(0x10, ZERO, SET, "Interrupts disabled")

    # Stop, 24h, 36.768 KHz crystal
    write_reg(0x11, 0x04)

    # Initialize time
    write_reg(0x00, 0)
    write_reg(0x01, 12)
    write_reg(0x02, 30)
    write_reg(0x03, 23)
    write_reg(0x04, 5)
    write_reg(0x05, 23)
    write_reg(0x06, 25)
    write_reg(0x07, 5)

    hsecs = check_reg(0x00, bits(0), SET, "Value set")
    check_reg(0x01, bits(12), SET, "Value set")
    check_reg(0x02, bits(30), SET, "Value set")
    check_reg(0x03, bits(23), SET, "Value set")
    check_reg(0x04, bits(5), SET, "Value set")
    check_reg(0x05, bits(23), SET, "Value set")
    check_reg(0x06, bits(25), SET, "Value set")
    check_reg(0x07, bits(5), SET, "Value set")

    # Run, 24h, 4MHz crystal
    write_reg(0x11, 0x0f)

    time.sleep(0.1)
    updated = read_reg(0x00)
    test(hsecs['data'] != updated['data'], True, "Hsecs updates after counter is enabled.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                    prog='icm7170.py',
                    description='Tests ICM7170 chip',
                    epilog='')
    parser.add_argument('--port', type=str, default="/dev/ttyACM0")
    parser.add_argument('--debug', action='store_true', default=False)

    args = parser.parse_args()

    tester = Tester(port = args.port, baudrate = 576000, DEBUG = args.debug)

    try:
        print("Testing ICM7170")
        tester.reset()

        test_rtc()

        assert failures == 0, "Some tests have failed."
        print("Test done!")
        tester.success()

    except AssertionError:
        tester.fail()
