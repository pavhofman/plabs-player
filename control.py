#!/usr/bin/python3

# usage: python control.py
#
# For lists of commands, events and properties consult the mpv reference:
#
#   http://mpv.io/manual/stable/#list-of-input-commands
#   http://mpv.io/manual/stable/#list-of-events
#   http://mpv.io/manual/stable/#property-list
#
import logging
import signal
import sys

import serial

from config import SERIAL_PORT, BAUDRATE, USE_SERIAL, LOG_FILE
from display import Display
from inputreader import InputReader
from player import Player
from serialreader import SerialReader


def getSerial() -> serial.Serial:
    # configure the serial connections
    ser = serial.Serial(
        port=SERIAL_PORT,
        baudrate=BAUDRATE,
        # blocking reading, since read in separate thread serialreader
        timeout=None,
        dsrdtr=False,
        xonxoff=False,
        rtscts=False,
        interCharTimeout=0,
        bytesize=8,
        parity=serial.PARITY_NONE,
        stopbits=1
    )

    ser.setRTS(0)
    ser.setDTR(0)
    return ser


def exitHandler(signum, frame):
    exitCleanly(0)


def exitCleanly(exitValue: int):
    if player is not None:
        player.close()
    if reader is not None:
        reader.stop()
        # the writer thread locks up at joining, therefore the timeout has to be specified
        reader.join(0.1)
    if ser is not None:
        ser.close()
    sys.exit(exitValue)


if __name__ == "__main__":
    logging.basicConfig(filename=LOG_FILE, level=logging.DEBUG, format='%(asctime)s %(levelname)s:%(message)s')
    ser = None
    reader = None
    player = None
    signal.signal(signal.SIGINT, exitHandler)
    signal.signal(signal.SIGTERM, exitHandler)
    try:
        reader = None
        display = None
        if (USE_SERIAL):
            ser = getSerial()
            serial.time.sleep(2)
            reader = SerialReader(ser)
            display = Display(ser)
        else:
            reader = InputReader()
            display = Display()

        reader.start()
        # Open the video player and load a file.
        player = Player(display)

        while True:
            reader.processCommand(player)
    except Exception as e:
        logging.error(e, exc_info=True)
        exitCleanly(1)
