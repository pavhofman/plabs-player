# maximum line length on display (font 2)
from collections import deque

from unidecode import unidecode

FONT2_MAXCHARS = 20
FONT2_MAXLINES = 3

FONT4_MAXCHARS = 12

PLAY_ICON = 1
PAUSE_ICON = 2


def chunkstring(string: str, length):
    return (string[0 + i:length + i] for i in range(0, len(string), length))


class AbstractScreen:
    def __init__(self, id: int):
        self.id = id
        self.icon = 0
        self.cdAvailable = False

    def setIsPlaying(self, isPlaying: bool):
        if isPlaying:
            self.icon = PAUSE_ICON
        else:
            self.icon = PLAY_ICON

    def setCDAvailable(self, cdAvailable: bool):
        self.cdAvailable = cdAvailable

    def setTracks(self, tracks: int):
        raise NotImplementedError()

    def setTrackNb(self, trackNb: int):
        raise NotImplementedError()

    def setText(self, text: str):
        raise NotImplementedError()

    def setStation(self, station: str):
        raise NotImplementedError()

    def setRadioTitle(self, title: str):
        raise NotImplementedError()

    def getMsg(self) -> bytes:
        raise NotImplementedError()

    def copyFrom(self, screen: 'AbstractScreen'):
        self.icon = screen.icon
        self.cdAvailable = screen.cdAvailable

    def _setLines(self, msg: str, lines: deque, maxChars: int, maxLines: int):
        # replacing utf-8 chars with ascii
        msg = unidecode(msg)
        lines.clear()
        #split, trim, copy first maxLines to lines
        index = 0
        for chunk in chunkstring(msg, maxChars):
            lines.append(chunk.strip())
            index += 1
            if index == maxLines:
                break

        # fill the remaining lines, if any
        while len(lines) < maxLines:
            lines.append('')
        return self
