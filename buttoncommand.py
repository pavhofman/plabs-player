from abstractcommand import AbstractCommand
from abstractplayer import AbstractPlayer

# defined in arduino!
SWITCH_BTN = 1
B2 = 2
B3 = 3
B4 = 4


class ButtonCommand(AbstractCommand):
    def __init__(self, button: int):
        self.__button = button

    def do(self, player: AbstractPlayer):
        player.handleButton(self.__button)
