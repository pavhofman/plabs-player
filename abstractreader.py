import logging
from queue import Queue
from threading import Thread, Event

from abstractplayer import AbstractPlayer

# defined in arduino!
INPUT_VOLUME_ID = b'V'
INPUT_BUTTON_ID = b'B'
INPUT_LOG_ID = b'L'


class AbstractReader(Thread):
    def __init__(self):
        # call the thread class
        super().__init__()
        self.__event = Event()
        # command queue - contains XXXCommands
        self.receiveQ = Queue()
        self.setDaemon(True)

    def stop(self):
        self.__event.set()

    def stopped(self) -> bool:
        return self.__event.isSet()

    def run(self):
        try:
            while not self.stopped():
                self.readFrame()
        except Exception as e:
            logging.error(e, exc_info=True)

    def readFrame(self):
        raise NotImplementedError()

    def processCommand(self, player: AbstractPlayer):
        command = self.receiveQ.get()
        command.do(player)
        self.receiveQ.task_done()
