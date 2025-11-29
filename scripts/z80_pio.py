#! /bin/env python3

import sys
import argparse
import serial

ZERO = b"00000000"
HIGHZ = b"ZZZZZZZZ"

DEBUG = False

tester = None

failures = 0

def test(actual, expected, info):
    global failures

    if actual != expected:
        failures = failures + 1
        print("Test failed: {}, {} != {}".format(info, expected, actual))

def send(command):
    tester.write(command + b"\n")

def read():
    return tester.read_until().strip()

def reset():
    send(b"r");

def fail():
    send(b"p0")
    send(b"f1")

def success():
    send(b"p1")
    send(b"f0")

def set_bar(value):
    send(b"b" + bytes("{0:08b}".format(value), 'latin1'))

def set_outputs(value):
    if DEBUG:
        print(value)
    send(b"o" + value)

def read_inputs():
    send(b"i")
    raw = read()
    value = {
        'data': raw[0:8],
        'portA': raw[8:16],
        'portB': raw[16:24],
        'interrupt': raw[24],
        'eout': raw[25]
    }
    if DEBUG:
        print(value)
    return value

# Z80 PIO:
# Data: I0-I7, O0-O7 via buffer
# PA: I8-I15, O8-O15, via buffer
# PB: I16-I23, O16-O23 via buffer
# /E: O26
# C/D: O25
# B/A: O24
# /M1: O29
# /IORQ: O28
# /RD: O27
# CLK: O30
# EIN: O31
# /INT: I24
# EOUT: I25

def set_pio(clk, m1, iorq, rd, ein, e, cd, ba, data, portA, portB):
    value = (data & 0xff) | ((portA & 0xff) << 8) | ((portB & 0xff) << 16)

    value = value | (ein << 31)
    value = value | (clk << 30)
    value = value | (m1 << 29)
    value = value | (iorq << 28)
    value = value | (rd << 27)
    value = value | (e << 26)
    value = value | (cd << 25)
    value = value | (ba << 24)

    set_outputs(bytes("{0:032b}".format(value), 'latin1'))

def pio_reset():
    # Run some clock cycles during reset.
    for i in range(30):
        set_pio(0, 1, 1, 1, 1, 1, 1, 1, 0x00, 0x00, 0x00)
        set_pio(1, 1, 1, 1, 1, 1, 1, 1, 0x00, 0x00, 0x00)
        read_inputs()

    # Induce reset
    for i in range(30):
        set_pio(0, 0, 1, 1, 1, 1, 1, 1, 0x00, 0x00, 0x00)
        set_pio(1, 0, 1, 1, 1, 1, 1, 1, 0x00, 0x00, 0x00)
        read_inputs()

    # Leave in known state.
    set_pio(0, 1, 1, 1, 1, 1, 1, 1, 0x00, 0x00, 0x00)

def m1_cycle():
    # M1 cycle
    set_pio(1, 1, 1, 1, 1, 1, 1, 1, 0x00, 0x00, 0x00)
    set_pio(0, 0, 1, 1, 1, 1, 1, 1, 0x00, 0x00, 0x00)
    read_inputs()
    set_pio(1, 0, 1, 0, 1, 1, 1, 1, 0x00, 0x00, 0x00)
    set_pio(0, 0, 1, 0, 1, 1, 1, 1, 0x00, 0x00, 0x00)
    read_inputs()
    set_pio(1, 0, 1, 0, 1, 1, 1, 1, 0x00, 0x00, 0x00)
    set_pio(0, 0, 1, 0, 1, 1, 1, 1, 0x00, 0x00, 0x00)
    read_inputs()
    set_pio(1, 1, 1, 1, 1, 1, 1, 1, 0x00, 0x00, 0x00)
    set_pio(0, 1, 1, 1, 1, 1, 1, 1, 0x00, 0x00, 0x00)
    read_inputs()

def send_word(cd, ba, data):
    set_pio(1, 1, 1, 1, 1, 0, cd, ba, data, 0x00, 0x00)
    set_pio(0, 1, 1, 1, 1, 0, cd, ba, data, 0x00, 0x00)
    read_inputs()

    set_pio(1, 1, 0, 1, 1, 0, cd, ba, data, 0x00, 0x00)
    set_pio(0, 1, 0, 1, 1, 0, cd, ba, data, 0x00, 0x00)
    read_inputs()

    set_pio(1, 1, 0, 1, 1, 0, cd, ba, data, 0x00, 0x00)
    set_pio(0, 1, 1, 1, 1, 0, cd, ba, data, 0x00, 0x00)
    read_inputs()

def test_pio_output():
    print("Resetting PIO")
    pio_reset()

    init = read_inputs()
    test(init['portA'], HIGHZ, "Port A floating after reset")
    test(init['portB'], HIGHZ, "Port B floating after reset")

    print("Set A as output")
    m1_cycle()
    send_word(1, 0, 0x0f)

    setupA = read_inputs()
    test(setupA['portA'], HIGHZ, "Port A floating after setup")

    print("Set B as output")
    m1_cycle()
    send_word(1, 1, 0x0f)

    setupB = read_inputs()
    test(setupB['portB'], HIGHZ, "Port B floating after setup")

    print("Write some data to A")
    m1_cycle()
    send_word(0, 0, 0x55)

    writeA = read_inputs()
    test(writeA['portA'], b"01010101", "Port A set")

    print("Write some data to B")
    m1_cycle()
    send_word(0, 1, 0x33)

    writeB = read_inputs()
    test(writeB['portB'], b"00110011", "Port B set")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                    prog='z80_pio.py',
                    description='Tests Z80 PIO chip',
                    epilog='')
    parser.add_argument('--port', type=str, default="/dev/ttyACM0")
    parser.add_argument('--debug', action='store_true', default=False)

    args = parser.parse_args()
    DEBUG = args.debug

    ser = serial.Serial(port = args.port, baudrate = 576000)

    with ser as s:
        tester = s
        try:
            print("Testing Z80 PIO")
            reset()

            test_pio_output()

            assert failures == 0, "Some tests have failed."
            print("Test done!")
            success()

        except AssertionError:
            fail()
