from struct import pack

from abstractscreen import AbstractScreen

ID = 5
# ID trackNb tracks playback-icon
FMT = 'b b b b'


class CDPlayingScreen(AbstractScreen):
    def __init__(self):
        super().__init__(ID)
        self.trackNb = 0
        self.tracks = 0

    def setTracks(self, tracks: int):
        self.tracks = tracks

    def setTrackNb(self, trackNb: int):
        self.trackNb = trackNb

    def getSerialMsg(self) -> bytes:
        return pack(FMT, self.id, self.trackNb, self.tracks, self.getIconCode())
