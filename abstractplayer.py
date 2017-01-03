class AbstractPlayer:
    def setVolume(self, volume):
        raise NotImplementedError

    def handleButton(self, button: int):
        raise NotImplementedError
