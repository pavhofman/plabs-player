import logging
import threading

import serial

from abstractplayer import AbstractPlayer
from control import getSerial
from display import Display
from serialreader import SerialReader


class TestPlayer(AbstractPlayer):
    def setVolume(self, volume):
        logging.debug("Volume:" + str(volume))

    def handleButton(self, button: int):
        logging.debug("Button:" + str(button))


def read_from_port(ser: serial.Serial):
    reader = SerialReader(ser)
    reader.start()

    player = TestPlayer()
    while True:
        reader.processCommand(player)



logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s:%(message)s')

ser = getSerial()
serial.time.sleep(2)

thread = threading.Thread(target=read_from_port, args=(ser,))
thread.start()
serial.time.sleep(1)

display = Display(ser)

display.showError("ahoj, tak co to tady planujete? Bude neco?")
serial.time.sleep(1)

display.showInfo("ahoj, tak co to tady planujete? Bude neco?")
serial.time.sleep(1)

display.setRadioScreen()
display.getScreen().setStation("Vltava")
display.getScreen().setRadioTitle("peknej narez tahleta stanice")
display.getScreen().setIsPlaying(False)
display.getScreen().setCDAvailable(False)
display.showScreen()
serial.time.sleep(1)

for i in range(8, 13):
    display.getScreen().setIsPlaying(True)
    display.showVolume(i)
    serial.time.sleep(0.1)
serial.time.sleep(1)
display.getScreen().setStation("Vltava je dlouhy nazev")
display.getScreen().setRadioTitle("peknej narez tahleta stanice")
display.showScreen()
serial.time.sleep(1)

display.showCDInfo("CD loading...")
serial.time.sleep(1)

display.showCDInfo("CD finished")
serial.time.sleep(1)

display.setCDPlayingScreen()
display.getScreen().setTracks(20)
isPlaying = True
for i in range(1, 5):
    display.getScreen().setTrackNb(i)
    isPlaying = not isPlaying
    display.getScreen().setIsPlaying(isPlaying)
    display.showScreen()
    serial.time.sleep(0.5)

for i in range(0, 5):
    display.getScreen().setIsPlaying(True)
    display.showVolume(i)
    serial.time.sleep(0.5)
serial.time.sleep(1)

for i in range(1, 5):
    display.getScreen().setTrackNb(i)
    isPlaying = not isPlaying
    display.getScreen().setIsPlaying(isPlaying)
    display.showScreen()
    serial.time.sleep(0.5)
