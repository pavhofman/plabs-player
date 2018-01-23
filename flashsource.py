from enum import Enum
from pathlib import Path

from typing import List

from buttoncommand import B2, B3, B7, B8, B4, B6
from display import Display
from extconfig import ExtConfig
from mixer import Mixer
from mpvsource import MPVSource
from mympv import MyMPV
from statefile import StateFile

ROOT_DIR = Path('/home/kluci/Hudba')
# maximum directory depth for recursive loadfile
MAX_DIR_DEPTH = 20


class Status(Enum):
    SELECT = 0
    PLAYBACK = 1


def getOrderedChildPaths(path: Path) -> List[Path]:
    return sorted(path.iterdir(), key=lambda k: str(k).lower())


class Dir:
    def __init__(self, path: Path):
        self.path = path
        self.index = 0  # type: int
        children = getOrderedChildPaths(path)
        self.items = [path] + children

    def getCurrentPath(self) -> Path:
        """
        return path corresponding to current index
        """
        return self.items[self.index]

    def decrIndex(self, status: Status) -> bool:
        limit = 0 if status == Status.SELECT else 1
        if self.index > limit:
            self.index = self.index - 1
            return True
        else:
            return False

    def incrIndex(self) -> bool:
        if self.index < len(self.items) - 1:
            self.index = self.index + 1
            return True
        else:
            return False


class FlashSource(MPVSource):
    def __init__(self, display: Display, extConfig: ExtConfig, stateFile: StateFile, mixer: Mixer, player):
        super().__init__(display, extConfig, stateFile, mixer, player)
        self._status = Status.SELECT
        self._curDir = None  # type: Dir

    def _start(self) -> None:
        # naplnit uvodni strukturu
        self._curDir = self._getDirItem(ROOT_DIR)

    def _displaySelf(self) -> None:
        if self._status == Status.SELECT:
            self._displaySelect()
        elif self._status == Status.PLAYBACK:
            self._displayPlayback()
        else:
            raise Exception("Unknown status " + str(self._status))

    def isAvailable(self) -> bool:
        return True

    def next(self) -> None:
        # TODO - in case of multiple items in playlist we must call  mpv "next"
        if self._curDir.incrIndex():
            if self._status == Status.PLAYBACK:
                self._stopPlaying()
                self._playCurrentItem()
            self._displaySelf()

    def prev(self) -> None:
        if self._curDir.decrIndex(self._status):
            if self._status == Status.PLAYBACK:
                self._stopPlaying()
                self._playCurrentItem()
            self._displaySelf()

    def handleButton(self, button: int):
        if button == B2:
            self.togglePause()
        elif button == B3 or button == B7:
            self.next()
        elif button == B4 or button == B8:
            self.prev()
        elif button == B6:
            self._handleB6()

    def _handleB6(self):
        if self._status == Status.PLAYBACK:
            self._stopPlaying()
            self._status = Status.SELECT
        elif self._status == Status.SELECT:
            self._playCurrentItem()
            self._status = Status.PLAYBACK

    def _playCurrentItem(self):
        if self._curDir is not None:
            path = self._curDir.getCurrentPath()
            if path.is_dir():
                self._appendChildrenToMPV(path=path, firstToPlay=True, level=0)
            else:
                self._startPlayback(path)

    def _startPlayback(self, path: Path):
        mpv = self._player.getMPV()  # type: MyMPV
        mpv.command("loadfile", str(path), "replace")
        mpv.play()

    def _appendToPlayback(self, path: Path):
        mpv = self._player.getMPV()  # type: MyMPV
        mpv.command("loadfile", str(path), "append")

    def _displaySelect(self):
        # we have to create the TreeMsg
        pass

    def _displayPlayback(self):
        self._display.showInfo("Playing file")

    def _getDirItem(self, path: Path) -> Dir:
        return Dir(path)

    def _appendChildrenToMPV(self, path: Path, firstToPlay: bool, level: int) -> None:
        """
        Recursive method for adding files in subtree to mpv playlist
        :param path: directory path
        :param firstToPlay: the first to-be-played track is played with startPlayback,
        all subsequent with appendToPlayback
        :param level: currect directory traversal depth
        """
        # sorted by case insensitive name
        for childPath in getOrderedChildPaths(path):
            if childPath.is_file():
                if firstToPlay:
                    self._startPlayback(childPath)
                    firstToPlay = False
                else:
                    self._appendToPlayback(childPath)
            elif level < MAX_DIR_DEPTH:
                self._appendChildrenToMPV(childPath, firstToPlay, level + 1)
