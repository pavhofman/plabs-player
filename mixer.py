import alsaaudio

from config import ALSA_CARD_INDEX


class AlsaError(Exception):
    pass


class Mixer:
    def __init__(self):
        self.__name = 'Master'
        self.__kwargs = {'cardindex': ALSA_CARD_INDEX}
        # muting at the beginning
        self.mute()

    def mute(self):
        # unfortunately on my soundcard muting mutes all playback controls, while unmuting unmutes only the specific control.
        # only setting volume to 0 instead
        self.setVolume(0)

    def getVolume(self) -> int:
        try:
            mixer = alsaaudio.Mixer(self.__name, **self.__kwargs)
            volumes = mixer.getvolume()
            # only the first channel, should be the same for all
            return volumes[0]
        except alsaaudio.ALSAAudioError as e:
            raise AlsaError(str(e))

    def setVolume(self, volume: int):
        try:
            mixer = alsaaudio.Mixer(self.__name, **self.__kwargs)
            channel = alsaaudio.MIXER_CHANNEL_ALL
            mixer.setmute(0, channel)
            mixer.setvolume(volume, channel)
        except alsaaudio.ALSAAudioError as e:
            raise AlsaError(str(e))
