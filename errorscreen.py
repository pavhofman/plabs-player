from collections import deque
from struct import pack

from abstractscreen import AbstractScreen, FONT2_MAXCHARS, FONT2_MAXLINES

ID = 1
# ID line1 line2 line3
FMT = 'b' + ' ' + str(FONT2_MAXCHARS + 1) + 's' + ' ' + str(FONT2_MAXCHARS + 1) + 's' + ' ' \
      + str(FONT2_MAXCHARS + 1) + 's'


class ErrorScreen(AbstractScreen):
    def __init__(self, id=ID):
        super().__init__(id)
        self.lines = deque(maxlen=FONT2_MAXLINES)
        self.setText("")

    def setText(self, msg: str):
        self._setLines(msg, self.lines, FONT2_MAXCHARS, FONT2_MAXLINES)

    def getSerialMsg(self) -> bytes:
        return pack(FMT, self.id, bytes(self.lines[0], 'utf-8'), bytes(self.lines[1], 'utf-8'),
                    bytes(self.lines[2], 'utf-8'))
