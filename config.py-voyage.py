# machine-specific config

SERIAL_PORT = '/dev/ttyS1'
BAUDRATE = 4800

DEV_CDROM = '/dev/cdrom'

ALSA_CARD_INDEX = 0
AUDIO_DEV = "alsa/plughw:CARD=SB,DEV=0"

# ext config
FLASH_LABEL = "RADIO"
PLAYLIST_FILENAME = "playlist.m3u"

# state file
STATE_DIR = "/var/lib/radio"
STATE_FILENAME = "radio.state"

IPC_SERVER_OPTION = "--input-ipc-server"
VOLUME_PROPERTY = "volume"

DST_IFS_DIR = "/etc/network/interfaces.d"

USE_SERIAL = True