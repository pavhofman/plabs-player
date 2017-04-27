from mpvsource import MPVSource

FILE = '/home/kluci/zvuk.wav'


class FlashSource(MPVSource):
    def _startPlaying(self) -> None:
        self._player.restartMPV()
        mpv = self._player.getMPV()
        mpv.command("loadfile", FILE)
        mpv.play()

    def _displaySelf(self) -> None:
        self._display.showCDInfo("Playing file")

    def isAvailable(self) -> bool:
        return True

    def next(self) -> None:
        pass

    def prev(self) -> None:
        pass
