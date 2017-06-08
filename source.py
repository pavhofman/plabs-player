from buttoncommand import B2, B3, B4, B6, B7, B8
from display import Display
from extconfig import ExtConfig
from mixer import Mixer
from statefile import StateFile


class Source():
    def __init__(self, display: Display, extConfig: ExtConfig, stateFile: StateFile, mixer: Mixer, player):
        self._display = display
        self._extConfig = extConfig
        self._stateFile = stateFile
        self._mixer = mixer
        self._player = player
        self._isActive = False

    def togglePause(self) -> None:
        raise NotImplementedError()

    def next(self) -> None:
        pass

    def prev(self) -> None:
        pass

    def isAvailable(self) -> bool:
        raise NotImplementedError()

    def setVolume(self, volume: int) -> None:
        if volume < 0:
            volume = 0
        elif volume > 99:
            volume = 99
        self._doSetVolume(volume)
        self._display.showVolume(volume)

    def _doSetVolume(self, volume):
        self._mixer.setVolume(volume)

    def activate(self) -> None:
        self._isActive = True
        self._startPlaying()
        self._displaySelf()

    def deactivate(self) -> None:
        self._stopPlaying()
        self._isActive = False

    def _displaySelf(self):
        raise NotImplementedError()

    def _startPlaying(self):
        raise NotImplementedError()

    def pause_changed(self, pause: bool):
        if pause is not None:
            self._display.showScreen()

    def chapterWasChanged(self, chapter: str):
        pass

    def _stopPlaying(self):
        pass

    def metadata_changed(self, metadata: dict):
        pass

    def isPaused(self):
        raise NotImplementedError()

    def handleButton(self, button: int):
        if button == B2 or button == B6:
            self.togglePause()
        elif button == B3 or button == B7:
            self.next()
        elif button == B4 or button == B8:
            self.prev()
