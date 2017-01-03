import configparser
import logging
import os

from config import STATE_DIR, STATE_FILENAME

DEFAULT_PLIST_POS = 0
PLIST_SECTION = 'playlist'
POSITION_KEY = 'last-playlist-position'


class StatusFileError(Exception):
    pass


class StateFile():
    def __init__(self):
        self.__dir = self.__getDir()
        self.__filePath = self.__getFilePath()
        self.__config = self.__readConfig()

    def close(self):
        pass

    def __del__(self):
        self.close()

    def __getDir(self):
        dir = STATE_DIR
        if not os.path.exists(dir):
            os.makedirs(dir)
        return dir

    def __getFilePath(self) -> str:
        path = os.path.join(self.__dir, STATE_FILENAME)
        if not os.path.exists(path):
            logging.debug("The state file " + path + " does not exist yet, creating")
            open(path, 'a').close()
        return path

    def __readConfig(self) -> configparser.ConfigParser:
        config = configparser.ConfigParser()
        config.read(self.__filePath)
        return config

    def getPlistPos(self) -> int:
        if self.__config is None or len(self.__config.sections()) == 0:
            return DEFAULT_PLIST_POS
        else:
            try:
                return self.__config.getint(PLIST_SECTION, POSITION_KEY)
            except:
                # section does not exist yet or incorrect value
                return DEFAULT_PLIST_POS

    def storePlistPos(self, plistPos: int):
        if (PLIST_SECTION not in self.__config.sections()):
            self.__config.add_section(PLIST_SECTION)
        self.__config.set(PLIST_SECTION, POSITION_KEY, str(plistPos))
        self.__storeFile()

    def __storeFile(self):
        with open(self.__filePath, 'w') as configfile:
            self.__config.write(configfile)
