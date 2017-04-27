from mpvsource import MPVSource
from statefile import DEFAULT_PLIST_POS


class RadioSource(MPVSource):
    def _displaySelf(self) -> None:
        self._display.setRadioScreen()

    def _startPlaying(self) -> None:
        self._player.restartMPV()
        mpv = self._player.getMPV()
        mpv.command("loadlist", self._extConfig.getPlaylistPath())
        mpv.play()

    def __setStoredPlistPos(self):
        self.__plistPos = self.__getStoredPlistPos()
        self.__setPlaylistPosition(self.__plistPos)

    def __getStoredPlistPos(self):
        plistPos = self._stateFile.getPlistPos()
        if (plistPos > self.__getPlaylistCount() - 1):
            plistPos = DEFAULT_PLIST_POS
        return plistPos

    def __setPlaylistPosition(self, plistPos):
        self._player.getMPV().set_property("playlist-pos", plistPos)
        self._stateFile.storePlistPos(plistPos)

    def __getPlaylistCount(self):
        positions = self._player.getMPV().get_property("playlist-count")
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

    def isAvailable(self) -> bool:
        return True
