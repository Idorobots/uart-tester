# UART tester

## STM32 UART via USB
Repo: https://github.com/rogerclarkmelbourne/STM32duino-bootloader
File: `generic_boot20_pc13.bin`
Upload with `stlink flash` to address 0x08000000.
Set `upload_protocol` to `dfu`.
Set build-flags to:
```
build_flags =
    -D PIO_FRAMEWORK_ARDUINO_ENABLE_CDC
    -D USBCON
```

PA11 and PA12 are used for USB communication and can't be used.

## Commands
### Reset
`r`

Resets the state of the tester.

### Input
`i`

Reads the inputs returning 0 or 1 or Z if the input is floating for each of the 32 inputs.

### Output
`oNNNN`

Writes the N bytes to the shift register. It's binary, little endian format for speed as the serial connection is on the slower side.

### Pass
`pX`

Toggles the pass LED. X is 1 or 0.

### Fail
`fX`

Toggles the fail LED, X is 1 or 0.

### Bar
`bXXXXXXXX`

Sets the state of the bar graph. X is 0 or 1.

## Hardware
The tester uses several 74HCT595 and 74HCT165 shift registers to provide 32 inputs and 32 outputs. There are optional LEDs for indicating a bar graph and pass/fail state.
