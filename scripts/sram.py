#! /bin/env python3

import sys
import argparse
from tester import Tester

# A test for CMOS SRAM chips.

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

PATTERNS = [b"10101010", b"01010101", b"11110000", b"00001111", b"11001100", b"00110011", b"11111111", b"00000000"];

ZERO = b"00000000"
HIGHZ = b"ZZZZZZZZ"

READWRITE = True
RETENTION = False
SIZING = False

tester = None
failures = 0

def test(actual, expected, addr, info):
    global failures

    if actual != expected:
        failures = failures + 1
        print("Test failed: {}, {} != {} at address {:04x}".format(info, expected, actual, addr))

def check_sram(cs2_pin, we, oe, cs1, cs2, addr, data_str):
    value = int(data_str, 2)
    value = value | (addr << 8)
    if not we:
        value = value | (1 << 31)
    if not oe:
        value = value | (1 << 30)
    if not cs1:
        value = value | (1 << 29)
    if cs2_pin != None and cs2:
        value = value | (1 << cs2_pin)

    tester.set_outputs(value)
    return tester.read_inputs()[-8:]

def test_sram(cs2_pin, addr_lines):
    test(check_sram(cs2_pin, False, False, False, True, 0x0000, ZERO), HIGHZ, 0x0000, "Outputs floating when no CS1")

    if cs2_pin != None:
        test(check_sram(cs2_pin, False, False, False, False, 0x0000, ZERO), HIGHZ, 0x0000, "Outputs floating when no CS")
        test(check_sram(cs2_pin, False, False, True, False, 0x0000, ZERO), HIGHZ, 0x0000, "Outputs floating when no CS2")

    addr_max = 2**addr_lines
    toggle = True

    # Check if memory size is correct
    if SIZING:
        for addr in range(0, addr_max):
            if(addr % 128 == 0):
                toggle = not toggle
                tester.set_bar(toggle and 1 or 0)
            test(check_sram(cs2_pin, True, False, True, True, addr, ZERO), ZERO, addr, "Write zeros")

        needle = b"10100101"
        test(check_sram(cs2_pin, True, False, True, True, 0x0000, needle), needle, 0x0000, "Store needle")

        for addr in range(1, addr_max):
            if(addr % 128 == 0):
                toggle = not toggle
                tester.set_bar(toggle and 1 or 0)
            test(check_sram(cs2_pin, False, True, True, True, addr, ZERO), ZERO, addr, "Needle not in haystack")

    if READWRITE:
        for i, pattern in enumerate(PATTERNS):
            b = (1 << (i + 1)) - 1
            tester.set_bar(b)

            print("Pattern: ", pattern)

            for addr in range(addr_max):
                if(addr % 128 == 0):
                    toggle = not toggle
                    tester.set_bar(toggle and (b | (1 << i)) or (b & ~(1 << i)))

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
                        tester.set_bar(toggle and (b | (1 << i)) or (b & ~(1 << i)))
                    # Read data back
                    test(check_sram(cs2_pin, False, True, True, True, addr, ZERO), pattern, addr, "Data retained")
                    # Turn off
                    test(check_sram(cs2_pin, False, False, False, False, addr, ZERO), HIGHZ, addr, "Floating after read")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                    prog='sram.py',
                    description='Tests 8k, 32k and 512k SRAM chips',
                    epilog='')
    parser.add_argument('--port', type=str, default="/dev/ttyACM0")
    parser.add_argument('-s', '--size', type=int, choices=[8, 32, 128, 256, 512])
    parser.add_argument('--retention', action='store_true', default=False)
    parser.add_argument('--sizing', action='store_true', default=False)
    parser.add_argument('--no-read-write', action='store_false', default=True)
    parser.add_argument('--debug', action='store_true', default=False)

    args = parser.parse_args()
    RETENTION = args.retention
    SIZING = args.sizing
    READWRITE = args.no_read_write

    tester = Tester(args.port, baudrate = 576000, DEBUG = args.debug)

    try:
        print("Testing {}k SRAM".format(args.size))
        tester.reset()

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
        tester.success()

    except AssertionError:
        tester.fail()
