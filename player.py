import logging
import time
from itertools import cycle

from abstractplayer import AbstractPlayer
from buttoncommand import SWITCH_BTN, PLAY_PAUSE_BTN, UP_BTN, DOWN_BTN
from cdsource import CDSource
from display import Display
from extconfig import ExtConfig
from flashsource import FlashSource
from mixer import Mixer
from mympv import MyMPV
from networkinfo import getNetworkInfo, NetworkInfo
from radiosource import RadioSource
from source import Source
from statefile import StateFile


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
        # precaution initial muting
        self.__mixer.mute()
        self.__stateFile = StateFile()
        self.__display = display
        self.__showInitInfo()
        self.__cdIsOver = False
        self.__mpv = MyMPV(self)
        self.__extConfig = self.__initExtConfig()
        # initial mute - arduino will send proper volumecommand
        # self.__switchToRadio()
        radioSource = RadioSource(display, self.__extConfig, self.__stateFile, self.__mixer, self)
        cdSource = CDSource(display, self.__extConfig, self.__stateFile, self.__mixer, self)
        flashSource = FlashSource(display, self.__extConfig, self.__stateFile, self.__mixer, self)
        self.__sources = [radioSource, cdSource, flashSource]
        self.__ringSources = cycle(self.__sources)
        self.switch()

    def __showInitInfo(self):
        try:
            nInfo = getNetworkInfo()
            if nInfo is not None:
                msg = self.__formatInitInfoMsg(nInfo)
                self.__display.showInfo(msg)
                # waiting to make the message readable
                time.sleep(1)
            else:
                self.__display.showError("Network not configured!")
                time.sleep(1)
        except Exception as e:
            logging.error(e, exc_info=True)
            raise e

    def __formatInitInfoMsg(self, nInfo: NetworkInfo) -> str:
        msg = "IF: " + nInfo.ifName
        msg += " " + "addr: " + nInfo.addr
        msg += " " + "ssid: " + str(nInfo.ssid)
        if nInfo.link:
            msg += " " + "link: " + str(nInfo.link) + "/70"
        return msg

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

    def switch(self):
        nextAvailableSource = self.__findNextAvailableSource()
        if (nextAvailableSource is not None):
            self.__switchToSource(nextAvailableSource)

    def __findNextAvailableSource(self):
        for i in range(0, len(self.__sources)):
            source = next(self.__ringSources)
            if (source.isAvailable()):
                return source
        return None

    def __switchToSource(self, source):
        if self.__selectedSource is not None:
            self.__selectedSource.deactivate()
        self.__selectedSource = source
        source.activate()

    def togglePause(self):
        if (self.__selectedSource is not None):
            self.__selectedSource.togglePause()

    def next(self):
        if (self.__selectedSource is not None):
            self.__selectedSource.next()

    def prev(self):
        if (self.__selectedSource is not None):
            self.__selectedSource.prev()

    def close(self):
        self.__display.showInfo("The control software is shut down")
        self.__mixer.mute()
        self.__mpv.close()
        self.__display.close()
        self.__extConfig.close()

    def getMPV(self) -> MyMPV:
        return self.__mpv

    def restartMPV(self):
        if self.__mpv is not None:
            self.__mpv.close()
        self.__mpv = MyMPV(self)

    def getSelectedSource(self) -> Source:
        return self.__selectedSource
