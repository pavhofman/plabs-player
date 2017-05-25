from struct import pack

from abstractscreen import AbstractScreen

ID = 3
# id volume playback-icon cdAvailable
FMT = 'b b b b'


class VolumeScreen(AbstractScreen):
    def __init__(self):
        super().__init__(ID)
        self.volume = 0

    def setVolume(self, volume: int):
        self.volume = volume

    def getSerialMsg(self) -> bytes:
        return pack(FMT, self.id, self.volume, self.getIconCode(), self.isCDAvailable())
