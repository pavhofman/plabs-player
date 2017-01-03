from abstractcommand import AbstractCommand
from abstractplayer import AbstractPlayer

# defined in arduino!
SWITCH_BTN = 1
PLAY_PAUSE_BTN = 2
UP_BTN = 3
DOWN_BTN = 4


class ButtonCommand(AbstractCommand):
    def __init__(self, button: int):
        self.__button = button

    def do(self, player: AbstractPlayer):
        player.handleButton(self.__button)
