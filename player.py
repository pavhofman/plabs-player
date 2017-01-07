import logging
import time

import pyudev
from pyudev import Devices
from pyudev import Monitor
from pyudev import MonitorObserver

from abstractplayer import AbstractPlayer
from buttoncommand import SWITCH_BTN, PLAY_PAUSE_BTN, UP_BTN, DOWN_BTN
from config import DEV_CDROM
from display import Display
from extconfig import ExtConfig
from mixer import Mixer
from mpv import MPVCommandError
from mympv import MyMPV
from networkinfo import getNetworkInfo
from statefile import StateFile, DEFAULT_PLIST_POS

MPV_VOLUME_THRESHOLD = 20

METADATA_TITLE_FIELD = 'icy-title'
METADATA_NAME_FIELD = 'icy-name'

MEDIA_TRACK_COUNT_AUDIO_UDEV_TAG = 'ID_CDROM_MEDIA_TRACK_COUNT_AUDIO'
DISK_EJECT_REQUEST_UDEV_TAG = 'DISK_EJECT_REQUEST'

CD_MODE = 1
RADIO_MODE = 2
CD_FILENAME = "cdda://"


class CDError(Exception):
    pass


class Player(AbstractPlayer):
    # current mode of the player
    __mode = None
    __mpv = None

    # current playlist position
    # cannot be read from the playlist_pos property as not-working streams cause mpv
    # fall back to the previous position automatically,
    # making thus the faulty stream unskippable
    __plistPos = 0

    # -------------------------------------------------------------------------
    # Initialization.
    # -------------------------------------------------------------------------
    def __init__(self, display: Display):
        self.__mixer = Mixer()
        self.__stateFile = StateFile()
        self.__display = display
        self.__showInitInfo()
        self.__cdIsOver = False

        self.__extConfig = self.__initExtConfig()
        self.__registerUdevCallback()
        # initial mute - arduino will send proper volumecommand
        self.__switchToRadio()
        self.__doSetVolume(0)

    def __showInitInfo(self):
        while True:
            try:
                nInfo = getNetworkInfo()
                if nInfo is not None:
                    msg = "IF: " + nInfo.ifName
                    msg += " " + "addr: " + nInfo.addr
                    msg += " " + "ssid: " + str(nInfo.ssid)
                    if nInfo.link:
                        msg += " " + "link: " + str(nInfo.link) + "/70"
                    self.__display.showInfo(msg)
                    # waiting to make the message readable
                    time.sleep(1)
                    break
                else:
                    self.__display.showError("Network not configured!")
                    time.sleep(1)
            except Exception as e:
                logging.error(e)
                raise e

    def handleButton(self, button: int):
        if button == SWITCH_BTN:
            self.switch()
        elif button == PLAY_PAUSE_BTN:
            self.togglePause()
        elif button == UP_BTN:
            self.next()
        elif button == DOWN_BTN:
            self.prev()

    def setVolume(self, volume: int):
        self.__doSetVolume(volume)
        self.__display.showVolume(volume)

    def __doSetVolume(self, volume):
        self.__mixer.setVolume(volume)
        self.__setMPVVolume(volume)

    def __setMPVVolume(self, volume):
        if volume < MPV_VOLUME_THRESHOLD:
            self.__mpv.setVolume(volume * (100 / MPV_VOLUME_THRESHOLD))
        else:
            # full volume
            self.__mpv.setVolume(100)

    def __initExtConfig(self) -> ExtConfig:
        try:
            return ExtConfig()
        except Exception as e:
            print(str(e))
            self.__display.showError(str(e))
            # allow for message propagation
            time.sleep(2)
            # finishing
            raise e

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

    def __restartMPV(self):
        if self.__mpv is not None:
            self.__mpv.close()
        self.__mpv = MyMPV(self)

    @staticmethod
    def __isCDInserted() -> bool:
        # using another udev context - running in a different thread
        try:
            context = pyudev.Context()
            device = Devices.from_device_file(context, DEV_CDROM)
            return MEDIA_TRACK_COUNT_AUDIO_UDEV_TAG in device
        except Exception:
            return False

    def __displayCDTracks(self):
        if self.__cdIsOver:
            self.__display.showCDInfo("End of CD")
        else:
            trackNb, tracks = self.__readCDFromMPV()
            self.__display.setCDPlayingScreen()
            self.__display.getScreen().setTrackNb(trackNb + 1)
            self.__display.getScreen().setTracks(tracks)
            self.__display.showScreen()

    def switch(self):
        if self.__mode == RADIO_MODE:
            if self.__isCDInserted():
                # we can switch to CD
                try:
                    self.__switchToCD()
                except CDError:
                    self.__switchToRadio()
        else:
            self.__switchToRadio()

    def __switchToCD(self):
        if self.__isCDInserted():
            self.__doSwitchToCD()

    def __doSwitchToCD(self):
        self.__mode = CD_MODE
        self.__display.showCDInfo("Reading CD")

        self.__restartMPV()
        self.__mpv.command("loadfile", CD_FILENAME)

    def __switchToRadio(self):
        self.__mode = RADIO_MODE
        self.__display.setRadioScreen()
        self.__display.getScreen().setCDAvailable(self.__isCDInserted())
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

    def __cdWasRemoved(self):
        self.__display.getScreen().setCDAvailable(False)
        if self.__mode == CD_MODE:
            self.__switchToRadio()
        self.__display.showScreen()

    def __cdWasInserted(self):
        self.__display.getScreen().setCDAvailable(True)
        self.__display.showScreen()

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

    def next(self):
        if self.__mode == CD_MODE:
            try:
                self.__nextCDTrack()
            except CDError:
                self.__switchToRadio()
        else:
            self.__nextRadioStream()

    def prev(self):
        if self.__mode == CD_MODE:
            try:
                self.__prevCDTrack()
            except CDError:
                self.__switchToRadio()
        else:
            self.__prevRadioStream()

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

    def __readCDFromMPV(self) -> (int, int):
        tracks = None
        trackNb = None
        waitTimer = 0
        while tracks is None and waitTimer < 20:
            try:
                tracks = self.__mpv.get_property("chapters")
                trackNb = self.__mpv.get_property("chapter")
            except MPVCommandError:
                # we have to wait a bit
                waitTimer += 1
                time.sleep(1)
        if tracks is None:
            raise CDError("cannot read CD")
        else:
            return trackNb, tracks

    def __setPlaylistPosition(self, plistPos):
        self.__mpv.set_property("playlist-pos", plistPos)
        self.__stateFile.storePlistPos(plistPos)

    def __getPlaylistCount(self):
        positions = self.__mpv.get_property("playlist-count")
        return positions

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

    def chapterWasChanged(self, chapter: str):
        if chapter is None or chapter >= 0:
            if chapter is None:
                # end of CD
                self.__cdIsOver = True
            elif chapter >= 0:
                self.__cdIsOver = False
            self.__displayCDTracks()

    def metadata_changed(self, metadata: dict):
        if metadata is not None:
            changed = False
            if METADATA_NAME_FIELD in metadata:
                name = metadata[METADATA_NAME_FIELD]
                self.__display.getScreen().setStation(name)
                changed = True
            if METADATA_TITLE_FIELD in metadata:
                title = metadata[METADATA_TITLE_FIELD]
                self.__display.getScreen().setRadioTitle(title)
                changed = True
            if changed:
                self.__display.showScreen()

    def pause_changed(self, pause: bool):
        if pause is not None:
            self.__display.getScreen().setIsPlaying(not pause)
            self.__display.showScreen()

    def close(self):
        self.__display.showInfo("The control software is shut down")
        self.__mixer.mute()
        self.__mpv.close()
        self.__display.close()
        self.__extConfig.close()
