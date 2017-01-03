import time
from queue import Queue
from threading import Thread, Event

from serial import Serial


class SerialWriter(Thread):

    def __init__(self, ser: Serial):
        # call the thread class
        super(SerialWriter, self).__init__()
        self.__serial = ser
        self.__event = Event()
        self.__sendQ = Queue()
        self.setDaemon(True)

    def stop(self):
        self.__event.set()
        if self.__serial.isOpen():
            self.__serial.flushOutput()  # flush output buffer
            self.__serial.close()

    def stopped(self) -> bool:
        return self.__event.isSet()

    def run(self):

        try:
            self.__serial.flushOutput()  # flush output buffer
            time.sleep(1)

            while not self.stopped():
                bytes_msg = self.__sendQ.get()
                self.__serial.write(bytes_msg)
                self.__sendQ.task_done()
            self.__serial.close()

        except Exception as e:
            print("error communicating...: ")
            print(e)
            self.__serial.close()

    def send(self, bytes_msg: bytes):
        self.__sendQ.put(bytes_msg)