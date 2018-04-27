#!/usr/bin/python
# Initialize NiRis board
# - set up display - initial screen is RED to indicate no Bluetooth connectivity - LCD display IP
# - if Bluetooth paired screen become GREN and accept input to display messages on LCD

import time
import commands
import os
import Adafruit_CharLCD as LCD
import bluetooth

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

# Make list of button value, text, and backlight color.
buttons = ( (LCD.SELECT, 'Select', (1,1,1)),
            (LCD.LEFT,   'Left'  , (1,0,0)),
            (LCD.UP,     'Up'    , (0,0,1)),
            (LCD.DOWN,   'Down'  , (0,1,0)),
            (LCD.RIGHT,  'Right' , (1,0,1)) )

# State machine for Bluetooth
# 0 -> Waiting to start (press select)
# 1 -> waiting for connection
# 2 -> connected
state = 0

# Monitor push buttons
while True:
   # Bluetooth management
   if (state == 0):
      # Check if Select is pressed
      if lcd.is_pressed(LCD.SELECT):
         # Button is pressed, change the message and backlight.
         lcd.clear()
         # Set LCD plate color GREEN
         lcd.set_color(0.0, 1.0, 0.0)
         lcd.clear()
         lcd.message('Waiting\nconnection')
         state = 1
      # Check if Down is pressed
      if lcd.is_pressed(LCD.DOWN):
         # Button is pressed, change the message and backlight.
         lcd.clear()
         lcd.message('Shutdown\nin 5 sec.')
         time.sleep(5)
         lcd.clear()
         os.system("sudo poweroff")

   if (state == 1):
      # Set up Bluettoth
      # Restart Bluetooth and set for slave
      os.popen('sudo hciconfig hci0 reset')
      os.popen('sudo hciconfig hci0 piscan')

      print "Bluetooth initialization - set as slave"

      # Set up Bluetooth socket 
      server_socket=bluetooth.BluetoothSocket( bluetooth.RFCOMM )

      server_socket.bind(("", bluetooth.PORT_ANY))
      server_socket.listen(1)

      uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"


      # Waiting for connection
      # NOTE ! The line below waits for a connection blocking the loop !
      client_socket,address = server_socket.accept()
      # print "Accepted connection from ",address
      # Set LCD plate color BLUE
      lcd.set_color(0.0, 0.0, 1.0)
      lcd.clear()
      lcd.message('Connected\nBluetooth')
      state = 2

   if (state == 2):
      data = client_socket.recv(1024)
      lcd.clear()
      lcd.message(data)
      # print "Received: %s" % data
      if (data == 'q'):
         state = 0
         client_socket.close()
         server_socket.close()
         print "Closed Bluettoth - disconnected"
         # Set color LCD Red
         lcd.set_color(1.0, 0.0, 0.0)
         lcd.clear()
         lcd.message('Disconnected\nBluetooth')

