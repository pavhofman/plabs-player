from abstractscreen import AbstractScreen
from abstractwriter import AbstractWriter


class OutputWriter(AbstractWriter):

    def handleItem(self, item: str):
        print("SCREEN: " + item + "\n")

    def output(self, screen: 'AbstractScreen'):
        self.sendQ.put(screen.toString())
