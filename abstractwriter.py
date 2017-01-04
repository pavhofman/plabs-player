from queue import Queue
from threading import Thread, Event

from abstractscreen import AbstractScreen


class AbstractWriter(Thread):
    def __init__(self):
        # call the thread class
        super(AbstractWriter, self).__init__()
        self.__event = Event()
        self.sendQ = Queue()
        self.setDaemon(True)

    def stop(self):
        self.__event.set()

    def stopped(self) -> bool:
        return self.__event.isSet()

    def run(self):
        try:
            while not self.stopped():
                item = self.sendQ.get()
                self.handleItem(item)
                self.sendQ.task_done()

        except Exception as e:
            print("error communicating...: ")
            print(e)

    def handleItem(self, item):
        raise NotImplementedError()

    def send(self, screen: 'AbstractScreen'):
        raise NotImplementedError()
