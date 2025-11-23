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
