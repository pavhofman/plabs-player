from abstractcommand import AbstractCommand
from abstractplayer import AbstractPlayer

# defined in arduino!
# short press = B1 - B4
# long press = B5 - B8 (i.e. B1 + 4)
# handled by the player
B1 = 1
# the rest is handled by the sources
B2 = 2
B3 = 3
B4 = 4
B5 = 5
B6 = 6
B7 = 7
B8 = 8

class ButtonCommand(AbstractCommand):
    def __init__(self, button: int):
        self.__button = button

    def do(self, player: AbstractPlayer):
        player.handleButton(self.__button)
