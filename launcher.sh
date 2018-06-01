#!/bin/sh
# launcher.sh - starts  python program at startup

echo " $HOSTNAME : `hostname -I`"

cd /
cd /home/pi/bluetooth_Rpi3
sudo ./BLTest.py
cd /
