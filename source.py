from display import Display
from extconfig import ExtConfig
from statefile import StateFile


class Source():
    def __init__(self, display: Display, extConfig: ExtConfig, stateFile: StateFile):
        self.__display = display
        self.__extConfig = extConfig
        self.__stateFile = stateFile

    def togglePause(self) -> None:
        raise NotImplementedError()

    def next(self) -> None:
        raise NotImplementedError()

    def prev(self) -> None:
        raise NotImplementedError()

    def isAvailable(self) -> bool:
        raise NotImplementedError()

    def activate(self) -> None:
        raise NotImplementedError()
