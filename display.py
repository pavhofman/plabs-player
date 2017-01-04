import time
from threading import Timer

from abstractscreen import AbstractScreen
from cdinfoscreen import CDInfoScreen
from cdplayingcreen import CDPlayingScreen
from errorscreen import ErrorScreen
from infoscreen import InfoScreen
from outputwriter import OutputWriter
from radioscreen import RadioScreen
from serialwriter import SerialWriter
from volumescreen import VolumeScreen

VOL_TIMEOUT = 1

"""
socat -d -d pty,raw,echo=0 pty,raw,echo=0
cat < /dev/pts/3
echo "S" > /dev/pts/3


Pri kazde zmene libovolneho prvku posle cely seznam pres seriovy port,
aby se pri prvnim volani nastavilo vsechno a kdykoliv se to mohlo zesynchronizovat
Arduino se samo rozhodne, co zmeni (bude si take udrzovat seznam prvku)

blokovane cteni v hlavnim vlakne v control.py
"""

# singletons
RADIO_SCR = RadioScreen()
CD_INFO_SCR = CDInfoScreen()
CD_PLAYING_SCR = CDPlayingScreen()
ERROR_SCR = ErrorScreen()
INFO_SCR = InfoScreen()
VOLUME_SCR = VolumeScreen()


class Display:
    def __init__(self, ser=None):
        self.__timer = None
        if ser is not None:
            self.__writer = SerialWriter(ser)
        else:
            self.__writer = OutputWriter()
        self.__writer.start()
        time.sleep(.1)
        self.__screen = INFO_SCR

    def close(self):
        self.__writer.stop()
        # the writer thread locks up at joining, therefore the timeout has to be specified
        self.__writer.join(0.1)
        if self.__timer is not None:
            self.__close_timer()

    def __del__(self):
        self.close()

    def getScreen(self) -> AbstractScreen:
        return self.__screen

    def setRadioScreen(self):
        RADIO_SCR.copyFrom(self.__screen)
        # print("RADIO: copying from " + str(self.__screen))
        # print("has cd: " + str(self.__screen.cdAvailable))
        # print("")
        self.__screen = RADIO_SCR

    def setCDPlayingScreen(self):
        CD_PLAYING_SCR.copyFrom(self.__screen)
        self.__screen = CD_PLAYING_SCR

    def showScreen(self):
        # print("Showing screen " + str(self.__screen))
        # print("has cd: " + str(self.__screen.cdAvailable))
        # print("")
        self.__writer.send(self.__screen)

    def showCDInfo(self, text: str):
        CD_INFO_SCR.copyFrom(self.__screen)
        self.__screen = CD_INFO_SCR
        self.__screen.setText(text)
        self.showScreen()

    def showError(self, message: str):
        ERROR_SCR.copyFrom(self.__screen)
        self.__screen = ERROR_SCR
        self.__screen.setText(message)
        self.showScreen()

    def showInfo(self, message: str):
        INFO_SCR.copyFrom(self.__screen)
        self.__screen = INFO_SCR
        self.__screen.setText(message)
        self.showScreen()

    def showVolume(self, volume: int):
        self.__activate_timer()
        # filling the volume screen
        VOLUME_SCR.copyFrom(self.__screen)
        # print("VOLUME: copying from " + str(self.__screen))
        # print("has cd: " + str(self.__screen.cdAvailable))
        # print("")
        VOLUME_SCR.setVolume(volume)
        # displaying without changing the main screen
        self.__writer.send(VOLUME_SCR)

    def __activate_timer(self):
        if self.__timer is None:
            self.__start_timer()
        else:
            if self.__timer.is_alive():
                # cancel and reschedule
                self.__close_timer()
                # new timer
                self.__start_timer()

    def __start_timer(self):
        self.__timer = Timer(VOL_TIMEOUT, self.__timer_finished)
        self.__timer.setDaemon(True)

        self.__timer.start()

    def __close_timer(self):
        self.__timer.cancel()
        self.__timer.join()

    def __timer_finished(self):
        # just showing the main screen
        self.showScreen()
        self.__timer = None
