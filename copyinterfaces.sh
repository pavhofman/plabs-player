#! /bin/bash

LABEL=RADIO
MOUNTPOINT=/tmp/$LABEL

/bin/mkdir $MOUNTPOINT
/bin/mount -L $LABEL $MOUNTPOINT
/bin/cp $MOUNTPOINT/interfaces.d/*.conf /etc/network/interfaces.d/
/bin/umount $MOUNTPOINT
rmdir $MOUNTPOINT

