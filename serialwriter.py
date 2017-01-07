from serial import Serial

from abstractscreen import AbstractScreen
from abstractwriter import AbstractWriter
from serialreader import FRAME_STOP, FRAME_START


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
        # wrapping the item with FRAME_START/STOP
        outputBytes = bytearray()
        outputBytes.append(FRAME_START)
        outputBytes.extend(item)
        outputBytes.append(FRAME_STOP)
        self.__serial.write(outputBytes)

    def output(self, screen: 'AbstractScreen'):
        self.sendQ.put(screen.getSerialMsg())
