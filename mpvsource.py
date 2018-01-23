from display import Display
from extconfig import ExtConfig
from mixer import Mixer
from source import Source
from statefile import StateFile

MPV_VOLUME_THRESHOLD = 20
METADATA_NAME_FIELD = 'icy-name'
METADATA_TITLE_FIELD = 'icy-title'


class MPVSource(Source):
    def __init__(self, display: Display, extConfig: ExtConfig, stateFile: StateFile, mixer: Mixer, player):
        super().__init__(display, extConfig, stateFile, mixer, player)

    def togglePause(self):
        status = self.isPaused()
        if status is True:
            self._player.getMPV().play()
        else:
            self._player.getMPV().pause()
            # display is updated via event pause_changed

    def isPaused(self) -> bool:
        status = self._player.getMPV().get_property("pause")
        return status

    def _stopPlaying(self):
        self._player.getMPV().command("stop")

    def _doSetVolume(self, volume) -> None:
        self.__setMPVVolume(volume)
        super()._doSetVolume(volume)

    def __setMPVVolume(self, volume):
        if volume < MPV_VOLUME_THRESHOLD:
            mpvVolume = volume * (100 / MPV_VOLUME_THRESHOLD)
            self._player.getMPV().setVolume(mpvVolume)
        else:
            # full volume
            self._player.getMPV().setVolume(100)

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

