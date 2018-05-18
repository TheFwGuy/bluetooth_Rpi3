#!/usr/bin/python
# Initialize BLtest board

import sys
import time
import commands
import os
import bluetooth
from socket import error as socket_error
import thread
import threading

# Initialization


# Display IP address
print "IP WLAN: hostname -I"

# Set up Bluettoth
# Restart Bluetooth and set for slave
os.popen('sudo hciconfig hci0 reset')
os.popen('sudo hciconfig hci0 piscan')

print "Bluetooth initialization - set as slave"

# Set up Bluetooth socket 
server_socket=bluetooth.BluetoothSocket( bluetooth.RFCOMM )

port = 1
server_socket.bind(("",port))
server_socket.listen(1)

# State machine for Bluetooth
# 0 -> waiting for connection
# 1 -> connected
state = 0

# Monitor push buttons
while True:
   # Bluetooth management
   if (state == 0):
      # Waiting for connection
      # NOTE ! The line below waits for a connection blocking the loop !
      try:
         client_socket,address = server_socket.accept()
         print "Accepted connection from ",address
         state = 1
      except Exception as ex:
         template = "1) An exception of type {0} occurred. Arguments:\n{1!r}"
         message = template.format(type(ex).__name__, ex.args)
         print message

   if (state == 1):
      try:
         data = client_socket.recv(1024, 0x40)
         print "Received: %s" % data
         if (data == 'q'):
            state = 0
            print "Closed Bluettoth - disconnected"
      except Exception as ex:
         template = "2) An exception of type {0} occurred. Arguments:\n{1!r}"
         message = template.format(type(ex).__name__, ex.args)
         if type(ex).__name__ == "BluetoothError":
            if ex.args[0] == "(104, 'Connection reset by peer')":
               state = 0
#               client_socket.close()
#               server_socket.close()
               print "Closed Bluettoth - disconnected"
            elif ex.args[0] == "(11, 'Resource temporarily unavailable')":
               # Ignore
               a = ex.args[0]
            else:
               print message
         else:
            print message

