from struct import pack

from abstractscreen import AbstractScreen, FONT4_MAXCHARS

ID = 4
# ID
FMT = 'b' + ' ' + str(FONT4_MAXCHARS + 1) + 's'


class CDInfoScreen(AbstractScreen):
    def __init__(self):
        super().__init__(ID)
        self.text = ""

    def setText(self, text: str):
        self.text = text[0:FONT4_MAXCHARS]

    def getSerialMsg(self) -> bytes:
        return pack(FMT, self.id, bytes(self.text, 'utf-8'))
