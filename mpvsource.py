from display import Display
from extconfig import ExtConfig
from mixer import Mixer
from mympv import MyMPV
from source import Source
from statefile import StateFile

MPV_VOLUME_THRESHOLD = 20
METADATA_NAME_FIELD = 'icy-name'
METADATA_TITLE_FIELD = 'icy-title'


class MPVSource(Source):
    _mpv = None

    def __init__(self, display: Display, extConfig: ExtConfig, stateFile: StateFile, mixer: Mixer, mpv: MyMPV, player):
        super().__init__(display, extConfig, stateFile, mixer, player)
        self._mpv = mpv

    def togglePause(self):
        status = self.__isPaused()
        if status is True:
            self._mpv.play()
        else:
            self._mpv.pause()
            # display is updated via event pause_changed

    def __isPaused(self) -> bool:
        status = self._mpv.get_property("pause")
        return status

    def _restartMPV(self):
        if self._mpv is not None:
            self._mpv.close()
        self._mpv = MyMPV(self)

    def _doSetVolume(self, volume) -> None:
        self.__setMPVVolume(volume)
        super()._doSetVolume(volume)

    def __setMPVVolume(self, volume):
        if volume < MPV_VOLUME_THRESHOLD:
            mpvVolume = volume * (100 / MPV_VOLUME_THRESHOLD)
            self._mpv.setVolume(mpvVolume)
        else:
            # full volume
            self._mpv.setVolume(100)

    def metadata_changed(self, metadata: dict):
        if metadata is not None:
            changed = False
            if METADATA_NAME_FIELD in metadata:
                name = metadata[METADATA_NAME_FIELD]
                self._display.getScreen().setStation(name)
                changed = True
            if METADATA_TITLE_FIELD in metadata:
                title = metadata[METADATA_TITLE_FIELD]
                self._display.getScreen().setRadioTitle(title)
                changed = True
            if changed:
                self._display.showScreen()
