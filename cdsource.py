import logging
import time
from alsaaudio import Mixer

import pyudev
from pyudev import Devices
from pyudev import Monitor
from pyudev import MonitorObserver

from config import DEV_CDROM
from display import Display
from extconfig import ExtConfig
from mpv import MPVCommandError
from mpvsource import MPVSource
from statefile import StateFile


class CDSource(MPVSource):
    def __init__(self, display: Display, extConfig: ExtConfig, stateFile: StateFile, mixer: Mixer, player):
        super().__init__(display, extConfig, stateFile, mixer, player)
        self._cdIsInserted = self.__isCDInserted()
        self.__registerUdevCallback()

    def __registerUdevCallback(self):
        context = pyudev.Context()
        monitor = Monitor.from_netlink(context)
        monitor.filter_by(subsystem='block')
        observer = MonitorObserver(monitor, callback=self.__checkUdevEvent, name='monitor-observer')
        observer.start()

    def __checkUdevEvent(self, device: dict):
        if DISK_EJECT_REQUEST_UDEV_TAG in device:
            self.__cdWasRemoved()
        elif MEDIA_TRACK_COUNT_AUDIO_UDEV_TAG in device:
            self.__cdWasInserted()

    def __isCDInserted(self) -> bool:
        # using another udev context - running in a different thread
        try:
            context = pyudev.Context()
            device = Devices.from_device_file(context, DEV_CDROM)
            return MEDIA_TRACK_COUNT_AUDIO_UDEV_TAG in device
        except Exception:
            return False

    def _displaySelf(self) -> None:
        self._display.showCDInfo("Reading CD")

    def _start(self) -> None:
        self.__cdIsOver = False
        self._player.restartMPV()
        mpv = self._player.getMPV()
        mpv.command("loadfile", CD_FILENAME)

    def next(self) -> None:
        self.__nextCDTrack()

    def __nextCDTrack(self):
        if self.__cdIsOver:
            self._player.getMPV().command("loadfile", CD_FILENAME)
        else:
            trackNb, tracks = self.__readCDFromMPV()
            if trackNb < (tracks - 1):
                trackNb += 1
            else:
                # rollover
                trackNb = 0
            self._player.getMPV().set_property("chapter", trackNb)

    def __readCDFromMPV(self) -> (int, int):
        tracks = None
        trackNb = None
        waitTimer = 0
        while tracks is None and waitTimer < CD_READ_TRIES:
            try:
                tracks = self._player.getMPV().get_property("chapters")
                trackNb = self._player.getMPV().get_property("chapter")
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
            self._player.getMPV().command("loadfile", CD_FILENAME)
        else:
            trackNb, tracks = self.__readCDFromMPV()
            if trackNb > 0:
                trackNb -= 1
            else:
                # rollover
                trackNb = tracks - 1
            self._player.getMPV().set_property("chapter", trackNb)

    @staticmethod
    def isCDInserted() -> bool:
        # using another udev context - running in a different thread
        try:
            context = pyudev.Context()
            device = Devices.from_device_file(context, DEV_CDROM)
            return MEDIA_TRACK_COUNT_AUDIO_UDEV_TAG in device
        except Exception:
            return False

    def isAvailable(self) -> bool:
        return self._cdIsInserted

    def chapterWasChanged(self, chapter: str):
        if chapter is None or chapter >= 0:
            if chapter is None:
                # end of CD
                self.__cdIsOver = True
            elif chapter >= 0:
                self.__cdIsOver = False
            self.__displayCDTracks()

    def __displayCDTracks(self):
        if self.__cdIsOver:
            self._display.showCDInfo("End of CD")
        else:
            trackNb, tracks = self.__readCDFromMPV()
            self._display.setCDPlayingScreen()
            self._display.getScreen().setTrackNb(trackNb + 1)
            self._display.getScreen().setTracks(tracks)
            self._display.showScreen()

    def __cdWasRemoved(self):
        self._cdIsInserted = False
        if self._isActive:
            self._player.switch()
        else:
            self._display.showScreen()

    def __cdWasInserted(self):
        self._cdIsInserted = True
        self._display.showScreen()


CD_FILENAME = "cdda://"
CD_READ_TRIES = 20


class CDError(Exception):
    pass


MEDIA_TRACK_COUNT_AUDIO_UDEV_TAG = 'ID_CDROM_MEDIA_TRACK_COUNT_AUDIO'
DISK_EJECT_REQUEST_UDEV_TAG = 'DISK_EJECT_REQUEST'
