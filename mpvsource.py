from mympv import MyMPV
from source import Source


class MPVSource(Source):
    __mpv = None

    def togglePause(self):
        status = self.__isPaused()
        if status is True:
            self.__mpv.play()
        else:
            self.__mpv.pause()
            # display is updated via event pause_changed

    def __isPaused(self) -> bool:
        status = self.__mpv.get_property("pause")
        return status

    def __restartMPV(self):
        if self.__mpv is not None:
            self.__mpv.close()
        self.__mpv = MyMPV(self)
