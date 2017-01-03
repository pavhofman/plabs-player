from abstractcommand import AbstractCommand
from abstractplayer import AbstractPlayer


class VolumeCommand(AbstractCommand):
    def __init__(self, volume: int):
        self.__volume = volume

    def do(self, player: AbstractPlayer):
        player.setVolume(self.__volume)
