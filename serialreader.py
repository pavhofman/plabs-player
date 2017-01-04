import logging

from serial import Serial

from abstractreader import AbstractReader, INPUT_VOLUME_ID, INPUT_BUTTON_ID, INPUT_LOG_ID
from buttoncommand import ButtonCommand
from volumecommand import VolumeCommand

# defined in arduino!
FRAME_START = 254
FRAME_STOP = 253


class SerialReader(AbstractReader):
    def __init__(self, ser: Serial):
        # call the thread class
        super().__init__()
        self.__serial = ser
        self.__serial.flushInput()

    def stop(self):
        super().stop()
        if self.__serial.isOpen():
            self.__serial.flushInput()
            self.__serial.close()

    def readFrame(self):
        frameStart = self.__serial.read(1)
        if frameStart[0] == FRAME_START:
            frameType = self.__serial.read(1)
            if frameType == INPUT_VOLUME_ID:
                self.__readVolume()
            if frameType == INPUT_BUTTON_ID:
                self.__readButton()
            if frameType == INPUT_LOG_ID:
                self.__readLog()
        else:
            logging.warning("Skipping unknown FRAME_START: " + str(frameStart[0]))

    def __readVolume(self):
        volume = self.__serial.read(1)
        frameStop = self.__serial.read(1)
        if frameStop[0] == FRAME_STOP:
            # OK
            self.receiveQ.put(VolumeCommand(volume[0]))
        else:
            logging.warning("Skipping unknown FRAME_STOP: " + str(frameStop[0]))

    def __readButton(self):
        button = self.__serial.read(1)
        frameStop = self.__serial.read(1)
        if frameStop[0] == FRAME_STOP:
            # OK
            self.receiveQ.put(ButtonCommand(button[0]))
        else:
            logging.warning("Skipping unknown FRAME_STOP: " + str(frameStop[0]))

    def __readLog(self):
        count = 0
        error = False
        msg = ''
        while True:
            character = self.__serial.read(1)
            if character[0] == FRAME_STOP:
                break
            count += 1
            if count > 100:
                logging.warning("Skipping - no FRAME_STOP read while reading log contents")
                error = True
                break
            try:
                msg += character.decode('utf-8')
            except Exception:
                logging.error("Received non-ascii character " + str(character) + "in log message " + msg)
                error = True
                break
        if not error:
            # not using the queue, logging directly
            logging.debug("Arduino log: " + msg)
