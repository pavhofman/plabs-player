from serial import Serial

from abstractscreen import AbstractScreen
from abstractwriter import AbstractWriter


class SerialWriter(AbstractWriter):
    def __init__(self, ser: Serial):
        super().__init__()
        self.__serial = ser

    def stop(self):
        super().stop()
        if self.__serial.isOpen():
            self.__serial.flushOutput()  # flush output buffer
            self.__serial.close()

    def handleItem(self, item: bytes):
        self.__serial.write(item)

    def output(self, screen: 'AbstractScreen'):
        self.sendQ.put(screen.getSerialMsg())
