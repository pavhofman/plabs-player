from config import VOLUME_PROPERTY
from mpv import MPV


class MyMPV(MPV):
    # -------------------------------------------------------------------------
    # Initialization.
    # -------------------------------------------------------------------------

    # The mpv process and the communication code run in their own thread
    # context. This results in the callback methods below being run in that
    # thread as well.
    def __init__(self, player):
        # Pass a window id to embed mpv into that window. Change debug to True
        # to see the json communication.
        super().__init__(window_id=None, debug=False)
        self.__player = player

    # -------------------------------------------------------------------------
    # Callbacks
    # -------------------------------------------------------------------------

    # property change events:
    # "time-pos" -> on_property_time_pos().

    def on_property_chapter(self, chapter=None):
        self.__player.chapterWasChanged(chapter)

    def on_property_metadata(self, metadata=None):
        self.__player.metadata_changed(metadata)

    def on_property_pause(self, pause=None):
        self.__player.pause_changed(pause)

    # -------------------------------------------------------------------------
    # Commands
    # -------------------------------------------------------------------------
    # Many commands must be implemented by changing properties.
    def play(self):
        self.set_property("pause", False)

    def pause(self):
        self.set_property("pause", True)

    def setVolume(self, volume: int):
        try:
            self.set_property(VOLUME_PROPERTY, int(volume))
        except:
            # not running, no problem
            pass
