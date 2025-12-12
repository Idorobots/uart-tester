import serial

class Tester:

    def __init__(self, port, baudrate = 576000, DEBUG = False):
        self.tester = serial.Serial(port = port, baudrate = baudrate)
        self.DEBUG = DEBUG

    def send(self, command, value = None):
        self.tester.write(command)
        if value != None:
            self.tester.write(value)

    def read(self):
        return self.tester.read_until().strip()

    def reset(self):
        self.send(b"r");

    def fail(self):
        self.send(b"p0")
        self.send(b"f1")

    def success(self):
        self.send(b"p1")
        self.send(b"f0")

    def set_bar(self, value):
        self.send(b"b", (value & 0xff).to_bytes(1, byteorder = 'little'))

    def set_outputs(self, value):
        if self.DEBUG:
            print("o{0:032b}".format(value))
        self.send(b"o", (value & 0xffffffff).to_bytes(4, byteorder = 'little'))

    def read_inputs(self):
        self.send(b"i")
        value = self.read()
        if self.DEBUG:
            print("i" + value.decode('latin1'))
        return value
