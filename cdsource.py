import logging
import time

from mpv import MPVCommandError
from mpvsource import MPVSource
from player import CD_FILENAME, CD_READ_TRIES, CDError


class CDSource(MPVSource):
    def activate(self) -> None:
        self.__display.showCDInfo("Reading CD")
        self.__cdIsOver = False
        self.__restartMPV()
        self.__mpv.command("loadfile", CD_FILENAME)

    def next(self) -> None:
        self.__nextCDTrack()

    def __nextCDTrack(self):
        if self.__cdIsOver:
            self.__mpv.command("loadfile", CD_FILENAME)
        else:
            trackNb, tracks = self.__readCDFromMPV()
            if trackNb < (tracks - 1):
                trackNb += 1
            else:
                # rollover
                trackNb = 0
            self.__mpv.set_property("chapter", trackNb)

    def __readCDFromMPV(self) -> (int, int):
        tracks = None
        trackNb = None
        waitTimer = 0
        while tracks is None and waitTimer < CD_READ_TRIES:
            try:
                tracks = self.__mpv.get_property("chapters")
                trackNb = self.__mpv.get_property("chapter")
            except MPVCommandError:
                # we have to wait a bit
                waitTimer += 1
                time.sleep(1)
        if (tracks is None) or (trackNb is None):
            logging.warning("Cannot read CD even after %d tries, no more trying", CD_READ_TRIES)
            raise CDError("cannot read CD")
        else:
            return trackNb, tracks

    def prev(self) -> None:
        self.__prevCDTrack()

    def __prevCDTrack(self):
        if self.__cdIsOver:
            self.__mpv.command("loadfile", CD_FILENAME)
        else:
            trackNb, tracks = self.__readCDFromMPV()
            if trackNb > 0:
                trackNb -= 1
            else:
                # rollover
                trackNb = tracks - 1
            self.__mpv.set_property("chapter", trackNb)
