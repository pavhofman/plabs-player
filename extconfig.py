import logging
import os
import shutil
from pathlib import Path
from subprocess import check_output, CalledProcessError

from config import FLASH_LABEL, PLAYLIST_FILENAME

# path to the interfaces.d dir in on the source partition
UDISKS_CMD = '/usr/bin/udisks'
BLKID_CMD = '/sbin/blkid'
SRC_IFS_DIR = "interfaces.d"


class ExtConfigError(Exception):
    pass


class ExtConfig():
    def __init__(self):
        self.__partition = None
        self.__partition = self.__get_radio_partition(FLASH_LABEL)
        # print("Partition je " + self.__partition)
        self.__mountpoint = self.__mount(self.__partition)
        self.__playlistPath = None


    def close(self):
        if self.__partition is not None:
            self.__unmount(self.__partition)

    def getPlaylistPath(self) -> str:
        if self.__playlistPath is None:
            self.__playlistPath = self.__get_path(PLAYLIST_FILENAME)
        return self.__playlistPath

    def __copydir(self, source, dest):
        """Copy a directory structure overwriting existing files"""
        for root, dirs, files in os.walk(source):
            if not os.path.isdir(root):
                os.makedirs(root)
            for each_file in files:
                rel_path = root.replace(source, '').lstrip(os.sep)
                src_path = os.path.join(root, each_file)
                dest_path = os.path.join(dest, rel_path, each_file)
                shutil.copyfile(src_path, dest_path)
                logging.debug("copied " + src_path + " to " + dest_path)

    def __get_radio_partition(self, label: str) -> str:
        # blkid -L LABEL_NAME -> /dev/sdb1
        try:
            devices = check_output([BLKID_CMD, '-L', label]).splitlines()
            for device in devices:
                return device.decode("utf-8")
        except CalledProcessError:
            raise ExtConfigError("No " + label + " partition found")

    def __mount(self, partition: str) -> str:
        try:
            check_output([UDISKS_CMD, '--mount-options', 'ro', '--mount', partition])
        except Exception as e:
            raise ExtConfigError("Unable to mount " + partition + ": " + str(e))

        with open('/proc/mounts', 'r') as f:
            for line in f.readlines():
                parts = line.split()
                if parts[0] == partition:
                    return parts[1]

    def __unmount(self, partition: str):
        try:
            check_output([UDISKS_CMD, '--unmount', partition])
        except Exception as e:
            logging.exception(e)
            raise ExtConfigError("Unable to unmount " + partition + ": " + str(e))

    def __get_path(self, name: str) -> str:
        path = os.path.join(self.__mountpoint, name)
        file = Path(path)
        if file.exists():
            return path
        else:
            raise ExtConfigError(path + " not found")
