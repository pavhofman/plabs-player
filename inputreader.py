import logging

from abstractreader import AbstractReader, INPUT_VOLUME_ID, INPUT_BUTTON_ID, INPUT_LOG_ID
from buttoncommand import ButtonCommand
from volumecommand import VolumeCommand


class InputReader(AbstractReader):
    def readFrame(self):
        line = input("Enter command (V5, B1, LThis is log line):\n")
        if line.startswith(INPUT_VOLUME_ID.decode("utf-8")):
            volume = int(line[1:])
            self.receiveQ.put(VolumeCommand(volume))
        elif line.startswith(INPUT_BUTTON_ID.decode("utf-8")):
            button = int(line[1:])
            self.receiveQ.put(ButtonCommand(button))
        elif line.startswith(INPUT_LOG_ID.decode("utf-8")):
            logMessage = line[1:]
            logging.debug("Arduino log: " + logMessage)
        else:
            logging.warning("Unknown command " + line)
