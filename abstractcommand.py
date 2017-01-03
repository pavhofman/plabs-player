from abstractplayer import AbstractPlayer


class AbstractCommand:
    def do(self, player: AbstractPlayer):
        raise NotImplementedError()
