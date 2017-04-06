import logging
import time
from itertools import cycle

import pyudev
from pyudev import Devices

from abstractplayer import AbstractPlayer
from buttoncommand import SWITCH_BTN, PLAY_PAUSE_BTN, UP_BTN, DOWN_BTN
from cdsource import CDSource, CD_FILENAME, CD_READ_TRIES, CDError, MEDIA_TRACK_COUNT_AUDIO_UDEV_TAG
from config import DEV_CDROM
from display import Display
from extconfig import ExtConfig
from mixer import Mixer
from mpv import MPVCommandError
from mpvsource import MPV_VOLUME_THRESHOLD, METADATA_NAME_FIELD, METADATA_TITLE_FIELD
from mympv import MyMPV
from networkinfo import getNetworkInfo
from radiosource import RadioSource
from statefile import StateFile, DEFAULT_PLIST_POS

CD_MODE = 1
RADIO_MODE = 2


class Player(AbstractPlayer):
    # current mode of the player
    __mode = None
    __mpv = None
    __selectedSource = None

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
        self.__mpv = MyMPV(self)
        self.__extConfig = self.__initExtConfig()
        # initial mute - arduino will send proper volumecommand
        # self.__switchToRadio()
        radioSource = RadioSource(display, self.__extConfig, self.__stateFile, self.__mixer, self.__mpv, self)
        self.__doSetVolume(0)
        cdSource = CDSource(display, self.__extConfig, self.__stateFile, self.__mixer, self.__mpv, self)
        self.__sources = [radioSource, cdSource]
        self.__ringSources = cycle(self.__sources)
        self.switch()

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
                logging.error(e, exc_info=True)
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
        if (self.__selectedSource is not None):
            self.__selectedSource.setVolume(volume)

    def __doSetVolume(self, volume):
        self.__mixer.setVolume(volume)
        self.__setMPVVolume(volume)

    def __setMPVVolume(self, volume):
        if volume < MPV_VOLUME_THRESHOLD:
            mpvVolume = volume * (100 / MPV_VOLUME_THRESHOLD)
            self.__mpv.setVolume(mpvVolume)
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
        nextAvailableSource = None
        for i in range(0, len(self.__sources)):
            source = next(self.__ringSources)
            if (source.isAvailable()):
                nextAvailableSource = source
                break
        if (nextAvailableSource is not None):
            if self.__selectedSource is not None:
                self.__selectedSource.deactivate()
            self.__selectedSource = nextAvailableSource
            nextAvailableSource.activate()

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
        if (self.__selectedSource is not None):
            self.__selectedSource.togglePause()

    def __isPaused(self) -> bool:
        status = self.__mpv.get_property("pause")
        return status

    def next(self):
        if (self.__selectedSource is not None):
            self.__selectedSource.next()

    def prev(self):
        if (self.__selectedSource is not None):
            self.__selectedSource.prev()

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

    def __setPlaylistPosition(self, plistPos):
        self.__mpv.set_property("playlist-pos", plistPos)
        self.__stateFile.storePlistPos(plistPos)

    def __getPlaylistCount(self):
        positions = self.__mpv.get_property("playlist-count")
        return positions

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
