# maximum line length on display (font 2)
from collections import deque

import jsonpickle
from unidecode import unidecode

import globalvariables

FONT2_MAXCHARS = 20
FONT2_MAXLINES = 3

FONT4_MAXCHARS = 12

# to play, i.e. showing when paused
PLAY_ICON = 1
# to pause, i.e. showing when playing
PAUSE_ICON = 2


def chunkstring(string: str, length):
    return (string[0 + i:length + i] for i in range(0, len(string), length))


class AbstractScreen:
    def __init__(self, id: int):
        self.id = id

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

    def getSerialMsg(self) -> bytes:
        raise NotImplementedError()

    def copyFrom(self, screen: 'AbstractScreen'):
        # self.icon = screen.icon
        # self.cdAvailable = screen.cdAvailable
        pass

    def _setLines(self, msg: str, lines: deque, maxChars: int, maxLines: int):
        # replacing utf-8 chars with ascii
        msg = unidecode(msg)
        lines.clear()
        # split, trim, copy first maxLines to lines
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

    def toString(self) -> str:
        jsonStr = jsonpickle.encode(self)
        return jsonStr + "CD : " + str(self.isCDAvailable()) + " ICON: " + str(self.getIconCode())
        # return json.dumps(json.loads(jsonStr), sort_keys=True, indent=4)

    def getIconCode(self) -> int:
        if globalvariables.player is None:
            return PLAY_ICON
        if globalvariables.player.isPaused():
            return PLAY_ICON
        else:
            return PAUSE_ICON

    def isCDAvailable(self) -> bool:
        if globalvariables.player is None:
            return False
        return globalvariables.player.isCDInserted()
