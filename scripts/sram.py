#! /bin/env python3

import sys
import argparse
import serial

# A test for CMOS SRAM chips.

PATTERNS = [b"10101010", b"01010101", b"11110000", b"00001111", b"11001100", b"00110011", b"11111111", b"00000000"];
ZERO = b"00000000"
HIGHZ = ZERO #b"ZZZZZZZZ" # FIXME

DEBUG = True
RETENTION = False
tester = None

failures = 0

def test(actual, expected, addr, info):
    global failures

    if actual != expected:
        failures = failures + 1
        print("Test failed: {}, {} != {} at address {:04x}".format(info, expected, actual, addr))

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
    value = read()[-8:]
    if DEBUG:
        print(value)
    return value

# 512k SRAM (32 pin DIP):
# Data: I0-I7, O0-O7 via latch
# Address: O8-O26
# CS2: ---
# /CS1: O29
# /OE: O30
# /WE: O31

# 256k SRAM (32 pin DIP):
# Data: I0-I7, O0-O7 via latch
# Address: O8-O25
# CS2: O26
# /CS1: O29
# /OE: O30
# /WE: O31

# 128k SRAM (32 pin DIP):
# Data: I0-I7, O0-O7 via latch
# Address: O8-O24
# CS2: O26
# /CS1: O29
# /OE: O30
# /WE: O31

# 32k SRAM (28 pin DIP):
# Data: I0-I7, O0-O7 via latch
# Address: O8-O22
# CS2: ---
# /CS1: O29
# /OE: O30
# /WE: O31

# 8k SRAM (28 pin DIP):
# Data: I0-I7, O0 - O7 via latch
# Address: O8-O20
# CS2: O21
# /CS1: O29
# /OE: O30
# /WE: O31

def check_sram(cs2_pin, we, oe, cs1, cs2, addr, data_str):
    value = 0
    value = value | (addr << 8)
    if not we:
        value = value | (1 << 31)
    if not oe:
        value = value | (1 << 30)
    if not cs1:
        value = value | (1 << 29)
    if cs2_pin != None and cs2:
        value = value | (1 << cs2_pin)

    cmd = bytes("{0:032b}".format(value & 0xffffffff), 'latin1')[0:-8] + data_str

    set_outputs(cmd)
    return read_inputs()

def test_sram(cs2_pin, addr_lines):
    test(check_sram(cs2_pin, False, False, False, True, 0x0000, ZERO), HIGHZ, None, "Outputs floating when no CS1")

    if cs2_pin != None:
        test(check_sram(cs2_pin, False, False, False, False, 0x0000, ZERO), HIGHZ, None, "Outputs floating when no CS")
        test(check_sram(cs2_pin, False, False, True, False, 0x0000, ZERO), HIGHZ, None, "Outputs floating when no CS2")

    addr_max = 2**addr_lines

    for i, pattern in enumerate(PATTERNS):
        b = (1 << (i + 1)) - 1
        toggle = True
        set_bar(b)

        print("Pattern: ", pattern)

        for addr in range(addr_max):
            if(addr % 128 == 0):
                toggle = not toggle
                set_bar(toggle and (b | (1 << i)) or (b & ~(1 << i)))

            # Write data
            test(check_sram(cs2_pin, True, False, True, True, addr, pattern), pattern, addr, "Writing data works")
            # Turn off
            test(check_sram(cs2_pin, False, False, False, False, addr, ZERO), HIGHZ, addr, "Floating after write")
            # Read data back
            test(check_sram(cs2_pin, False, True, True, True, addr, ZERO), pattern, addr, "Reading data works")

        if RETENTION:
            for addr in range(addr_max):
                if(addr % 128 == 0):
                    toggle = not toggle
                    set_bar(toggle and (b | (1 << i)) or (b & ~(1 << i)))
                # Read data back
                test(check_sram(cs2_pin, False, True, True, True, addr, ZERO), pattern, addr, "Data retained")
                # Turn off
                test(check_sram(cs2_pin, False, False, False, False, addr, ZERO), HIGHZ, addr, "Floating after read")
    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                    prog='sram.py',
                    description='Tests 8k, 32k and 512k SRAM chips',
                    epilog='')
    parser.add_argument('--port', type=str, default="/dev/ttyACM0")
    parser.add_argument('-s', '--size', type=int, choices=[8, 32, 128, 256, 512])
    parser.add_argument('-r', '--retention', action='store_true', default=False)
    parser.add_argument('--debug', action='store_true', default=False)

    args = parser.parse_args()
    DEBUG = args.debug
    RETENTION = args.retention

    ser = serial.Serial(port = args.port, baudrate = 576000)

    with ser as s:
        tester = s
        try:
            print("Testing {}k SRAM".format(args.size))
            reset()

            if args.size == 512:
                 test_sram(None, 19)
            elif args.size == 256:
                 test_sram(26, 18)
            elif args.size == 128:
                 test_sram(26, 17)
            elif args.size == 32:
                 test_sram(None, 15)
            elif args.size == 8:
                 test_sram(21, 13)
            else:
                 print("Unsuported RAM size specified.")

            assert failures == 0, "Some tests have failed."
            print("Test done!")
            success()

        except AssertionError:
            fail()
