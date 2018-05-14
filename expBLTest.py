#!/usr/bin/python
# Initialize NiRis board
# - set up display - initial screen is RED to indicate no Bluetooth connectivity - LCD display IP
# - if Bluetooth paired screen become GREN and accept input to display messages on LCD

import time
import commands
import os
import errno
from socket import error as socket_error
import thread
import threading
import Adafruit_CharLCD as LCD
import bluetooth
import subprocess as sp

# Global variables

# Make list of button value, text, and backlight color.
buttons = ( (LCD.SELECT, 'Select', (1,1,1)),
            (LCD.LEFT,   'Left'  , (1,0,0)),
            (LCD.UP,     'Up'    , (0,0,1)),
            (LCD.DOWN,   'Down'  , (0,1,0)),
            (LCD.RIGHT,  'Right' , (1,0,1)) )

# State machine for Bluetooth
# 0 -> Initialization program - init BT 
# 1 -> waiting for connection
# 2 -> connected
state = 0

# Flag to informa about data read
isData = False

# Define functions

def waitBTthread():
   global state
   global server_socket
   global client_socket
   global address

   while True:
      if state == 1:
         lcd.set_color(1.0, 0.0, 1.0)
         # print "Start wait ..."
         # NOTE ! The line below waits for a connection blocking the loop !
         client_socket,address = server_socket.accept()
         # print "Accepted connection from ",address
         state = 2
         # Set LCD plate color BLUE
         lcd.set_color(0.0, 0.0, 1.0)
         lcd.clear()
         lcd.message('Connected\nBluetooth')

def readBTthread():
   global state
   global data
   global server_socket
   global client_socket
   global address
   global isData

   while True:
      if state == 2:
         if isData == False:
            try:
               data = client_socket.recv(1024)  # The function waits for characters !
               isData = True
            except:
               closeConnection()
               state = 0
               isData = False


def openConnection():
   global server_socket
   global client_socket
   global address

   # Set up Bluettoth
   # Restart Bluetooth and set for slave
   os.popen('sudo hciconfig hci0 reset')
   os.popen('sudo hciconfig hci0 piscan')

   print "Bluetooth initialization - set as slave"

   # Set up Bluetooth socket 
   server_socket=bluetooth.BluetoothSocket( bluetooth.RFCOMM )

   print "Use port_any : ", bluetooth.PORT_ANY 
   server_socket.bind(("", bluetooth.PORT_ANY))
   server_socket.listen(1)

#   if waitBTthread().is_alive():
#      print "Thread already running"
#   else:
      # Waiting for connection - start thread !
   print "Start thread  waiting for connection"
   t1 = threading.Thread(target= waitBTthread, args=())
   if t1.is_alive() == False:
      t1.start()


def closeConnection():
   global server_socket
   global client_socket
   global address

   client_socket.close()
   server_socket.close()
   print "Closed Bluetooth - disconnected"
   # Set color LCD Red
   lcd.set_color(1.0, 0.0, 0.0)
   lcd.clear()
   #lcd.message('Disconnected\nBluetooth')
   lcd.message('IP WLAN:\n')
   lcd.message(commands.getoutput('hostname -I'))

# Initialize the LCD using the pins
lcd = LCD.Adafruit_CharLCDPlate()

# create some custom characters
lcd.create_char(1, [2, 3, 2, 2, 14, 30, 12, 0])
lcd.create_char(2, [0, 1, 3, 22, 28, 8, 0, 0])
lcd.create_char(3, [0, 14, 21, 23, 17, 14, 0, 0])
lcd.create_char(4, [31, 17, 10, 4, 10, 17, 31, 0])
lcd.create_char(5, [8, 12, 10, 9, 10, 12, 8, 0])
lcd.create_char(6, [2, 6, 10, 18, 10, 6, 2, 0])
lcd.create_char(7, [31, 17, 21, 21, 21, 21, 17, 31])

# Initialization

# Start set up LCD plat RED
lcd.set_color(1.0, 0.0, 0.0)
lcd.clear()

# Display IP address
lcd.message('IP WLAN:\n')
lcd.message(commands.getoutput('hostname -I'))

# Monitor push buttons
# The main loop of the program check if the Select button is pressed.
# If is pressed, the shutdown is issued

isData = False;

t1 = threading.Thread(target= waitBTthread, args=())
t2 = threading.Thread(target= readBTthread, args=())

while True:
   # Check if Select is pressed
   if lcd.is_pressed(LCD.SELECT):
      # Button is pressed, change the message and backlight.
      lcd.clear()
      lcd.message('Shutdown\nin 5 sec.')
      time.sleep(5)
      lcd.clear()
      os.system("sudo poweroff")

   # Bluetooth management
   if (state == 0):
      print "Call openconnection"
      openConnection()   # The function waits until a connection happens !
      state = 1

#   if (state == 1):
#      print "."

   if (state == 2):
      try:
         data = client_socket.recv(1024, 0x40)  # The function waits for characters !
         isData = True
      except socket_error as serr:
         if serr.errno != 11:
            print "Errno : %d" % serr.errno
            closeConnection()
            state = 0

#      if t2.is_alive() == False:
#         t2.start()
#         print "Start thread  waiting for data"

      if isData:
         lcd.clear()
         lcd.message(data)
         print "Received: %s" % data
         if (data == 'q\n'):
            closeConnection()
            state = 0
         isData = False

      # Check if Down is pressed
      if lcd.is_pressed(LCD.DOWN):
         # Button is pressed, send message
         print "Down button pressed - send message"
         client_socket.send("Down")

