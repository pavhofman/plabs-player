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
        raise NotImplementedError()

    def prev(self) -> None:
        raise NotImplementedError()

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
        self._displaySelf()
        self._startPlaying()

    def deactivate(self) -> None:
        self._stopPlaying()
        self._isActive = False

    def _displaySelf(self):
        raise NotImplementedError()

    def _startPlaying(self):
        raise NotImplementedError()

    def pause_changed(self, pause: bool):
        if pause is not None:
            self._display.getScreen().setIsPlaying(not pause)
            self._display.showScreen()

    def chapterWasChanged(self, chapter: str):
        raise NotImplementedError()

    def _stopPlaying(self):
        pass
