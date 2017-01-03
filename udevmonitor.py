import pyudev as pyudev

MEDIA_TRACK_COUNT_AUDIO = 'ID_CDROM_MEDIA_TRACK_COUNT_AUDIO'

if __name__ == "__main__":
    context = pyudev.Context()
    monitor = pyudev.Monitor.from_netlink(context)
    monitor.filter_by('block')
    for device in iter(monitor.poll, None):
        if MEDIA_TRACK_COUNT_AUDIO in device:
            print("inserted with tracks " + device.get(MEDIA_TRACK_COUNT_AUDIO))
        elif 'DISK_EJECT_REQUEST' in device:
            print("ejected medium")

