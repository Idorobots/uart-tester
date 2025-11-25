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
    value = read()[-8:]
    if DEBUG:
        print(value)
    return value

# 32k SRAM:
# Data: I0-I8, O0-O8 via 100k
# Address: O8-O22
# /CS: O29
# /OE: O30
# /WE: 031

def check_32k_sram(we, oe, cs, addr, data_str):
    addr_str = bytes("{0:016b}".format(addr & 0xffff)[-15:], 'latin1')
    set_outputs((we and b"0" or b"1") + (oe and b"0" or b"1") + (cs and b"0" or b"1") + b"000000" + addr_str + data_str)
    return read_inputs()

def test_32k_sram():
    test(check_32k_sram(False, False, False, 0x0000, ZERO), HIGHZ, "Outputs floating when no CS")

    addr_max = 2**15

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
            test(check_32k_sram(True, False, True, addr, pattern), pattern, "Writing data works")
            # Turn off
            test(check_32k_sram(False, False, False, addr, ZERO), HIGHZ, "Floating after write")
            # Read data back
            test(check_32k_sram(False, True, True, addr, ZERO), pattern, "Reading data works")

        if RETENTION:
            for addr in range(addr_max):
                # Read data back
                test(check_32k_sram(False, True, True, addr, ZERO), pattern, "Data retained")
                # Turn off
                test(check_32k_sram(False, False, False, addr, ZERO), HIGHZ, "Floating after read")

# 8k SRAM:
# Data: I0-I8, O0 - O8 via 100k
# Address: O8-O20
# CS2: O21
# /CS1: O29
# /OE: O30
# /WE: 031

def check_8k_sram(we, oe, cs1, cs2, addr, data_str):
    addr_str = bytes("{0:016b}".format(addr & 0xffff)[-13:], 'latin1')
    set_outputs((we and b"0" or b"1") + (oe and b"0" or b"1") + (cs1 and b"0" or b"1") + b"0000000" + (cs2 and b"1" or b"0") + addr_str + data_str)
    return read_inputs()

def test_8k_sram():
    test(check_8k_sram(False, False, False, False, 0x0000, ZERO), HIGHZ, "Outputs floating when no CS")
    test(check_8k_sram(False, False, False, True, 0x0000, ZERO), HIGHZ, "Outputs floating when no CS1")
    test(check_8k_sram(False, False, True, False, 0x0000, ZERO), HIGHZ, "Outputs floating when no CS2")

    addr_max = 2**13

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
            test(check_8k_sram(True, False, True, True, addr, pattern), pattern, "Writing data works")
            # Turn off
            test(check_8k_sram(False, False, False, False, addr, ZERO), HIGHZ, "Floating after write")
            # Read data back
            test(check_8k_sram(False, True, True, True, addr, ZERO), pattern, "Reading data works")
        if RETENTION:
            for addr in range(addr_max):
                # Read data back
                test(check_8k_sram(False, True, True, True, addr, ZERO), pattern, "Data retained")
                # Turn off
                test(check_8k_sram(False, False, False, False, addr, ZERO), HIGHZ, "Floating after read")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                    prog='sram.py',
                    description='Tests 8k, 32k and 512k SRAM chips',
                    epilog='')
    parser.add_argument('--port', type=str, default="/dev/ttyACM0")
    parser.add_argument('-s', '--size', type=int, default=32)
    parser.add_argument('-r', '--retention', action='store_true', default=False)
    parser.add_argument('--debug', action='store_true', default=False)

    args = parser.parse_args()
    DEBUG = args.debug
    RETENTION = args.retention

    ser = serial.Serial(port = args.port, baudrate = 576000)

    with ser as s:
        tester = s
        try:
            reset()

            if args.size == 512:
                 pass
            elif args.size == 32:
                 print("Testing 32k SRAM")
                 test_32k_sram()
            elif args.size == 8:
                 print("Testing 8k SRAM")
                 test_8k_sram()
            else:
                 print("Unsuported RAM size specified.")

            assert failures == 0, "Some tests have failed."
            print("Test done!")
            success()

        except AssertionError:
            fail()
