from collections import deque
from struct import pack

from abstractscreen import AbstractScreen, FONT2_MAXCHARS, FONT4_MAXCHARS

TITLE_MAXLINES = 2
STATION_MAXLINES = 2

ID = 6
# ID station1 station2 title1 title2 playing cd-available
FMT = 'b' + ' ' + str(FONT4_MAXCHARS + 1) + 's' + ' ' + str(FONT4_MAXCHARS + 1) + 's' + ' ' \
      + str(FONT2_MAXCHARS + 1) + 's' + ' ' + str(FONT2_MAXCHARS + 1) + 's' + ' b b'


class RadioScreen(AbstractScreen):
    def __init__(self):
        super().__init__(ID)
        self.titleLines = deque(maxlen=TITLE_MAXLINES)
        self.stationLines = deque(maxlen=STATION_MAXLINES)
        self.clearLines(self.stationLines)
        self.clearLines(self.titleLines)

    def clearLines(self, lines: deque):
        lines.clear()
        lines.append("")
        lines.append("")

    def setStation(self, station: str):
        self._setLines(station, self.stationLines, FONT4_MAXCHARS, STATION_MAXLINES)
        self.clearLines(self.titleLines)

    def setRadioTitle(self, title: str):
        self._setLines(title, self.titleLines, FONT2_MAXCHARS, TITLE_MAXLINES)
        return self

    def getSerialMsg(self) -> bytes:
        return pack(FMT, self.id, bytes(self.stationLines[0], 'utf-8'), bytes(self.stationLines[1], 'utf-8'),
                    bytes(self.titleLines[0], 'utf-8'), bytes(self.titleLines[1], 'utf-8'), self.getIconCode(),
                    self.isCDAvailable())
