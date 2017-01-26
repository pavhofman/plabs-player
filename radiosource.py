from mpvsource import MPVSource
from statefile import DEFAULT_PLIST_POS


class RadioSource(MPVSource):
    def activate(self) -> None:
        self.__display.setRadioScreen()
        self.__restartMPV()
        self.__mpv.command("loadlist", self.__extConfig.getPlaylistPath())
        self.__setStoredPlistPos()
        self.__mpv.play()

    def __setStoredPlistPos(self):
        self.__plistPos = self.__getStoredPlistPos()
        self.__setPlaylistPosition(self.__plistPos)

    def __getStoredPlistPos(self):
        plistPos = self.__stateFile.getPlistPos()
        if (plistPos > self.__getPlaylistCount() - 1):
            plistPos = DEFAULT_PLIST_POS
        return plistPos

    def __setPlaylistPosition(self, plistPos):
        self.__mpv.set_property("playlist-pos", plistPos)
        self.__stateFile.storePlistPos(plistPos)

    def __getPlaylistCount(self):
        positions = self.__mpv.get_property("playlist-count")
        return positions

    def next(self) -> None:
        self.__nextRadioStream()

    def __nextRadioStream(self):
        count = self.__getPlaylistCount()
        if self.__plistPos < (count - 1):
            self.__plistPos += 1
        else:
            # rollover
            self.__plistPos = 0
        self.__setPlaylistPosition(self.__plistPos)

    def __prevRadioStream(self):
        positions = self.__getPlaylistCount()
        if self.__plistPos > 0:
            self.__plistPos -= 1
        else:
            # rollover
            self.__plistPos = positions - 1
        self.__setPlaylistPosition(self.__plistPos)

    def prev(self) -> None:
        self.__prevRadioStream()
