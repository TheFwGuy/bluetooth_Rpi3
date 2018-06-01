#!/usr/bin/python
# Initialize Raspberry Pi board
# If the LCD Char didplay is detected :
# - set p display - initial screen is RED to indicate no Bluetooth connectivity - LCD display IP
# - if Bluetooth paired screen become GREN and accept input to display messages on LCD
#
# If the LCD SSD1306 is detected
# - 

import time
import commands
import os
import subprocess
import errno
from socket import error as socket_error
import thread
import threading
import Adafruit_CharLCD as LCD
import Adafruit_SSD1306
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import bluetooth
import subprocess as sp

# Global variables
RST = None     # on the PiOLED this pin isnt used

# 128x32 display with hardware I2C:
disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST)

# Configuration :
#     0   -> No Display
#     1   -> LCD Char display
#     2   -> LCD SSD1306 display
#     3   -> TFT
LCDtype = 2

server_socket=bluetooth.BluetoothSocket( bluetooth.RFCOMM )

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
BTstate = 0

# Data TX/RX related variables
isDataIn = False
isDataOut = False
dataIn = "  "
dataOut = "  "

# Define functions

# Identify type display present
#def idDisplay():


# Bluetooth Thread
def waitBTthread():
	global BTstate
	global server_socket
	global isDataIn
	global isDataOut
	global dataIn
	global dataOut

	while True:
		time.sleep(.5)          # Give some time to the main loop
		if BTstate == 0:
			# Init connection
			server_socket=bluetooth.BluetoothSocket( bluetooth.RFCOMM )

			print "Use port_any : ", bluetooth.PORT_ANY 
			server_socket.bind(("", bluetooth.PORT_ANY))
			server_socket.listen(1)
			BTstate = 1

		if BTstate == 1:
			# print "Start wait ..."
			# NOTE ! The line below waits for a connection blocking the loop !
			try:
				client_socket,address = server_socket.accept()
				print "Accepted connection from ",address
				BTstate = 2
			except Exception as ex:
				template = "1) An exception of type {0} occurred. Arguments:\n{1!r}"
				message = template.format(type(ex).__name__, ex.args)
				print message

		if BTstate == 2:
			if isDataIn == False:
#				print "Wait RX"
				try:
					dataIn = client_socket.recv(1024, 0x40)  # The function waits for characters !
					isDataIn = True
				except Exception as ex:
					template = "2) An exception of type {0} occurred. Arguments:\n{1!r}"
					message = template.format(type(ex).__name__, ex.args)
					if type(ex).__name__ == "BluetoothError":
						if ex.args[0] == "(104, 'Connection reset by peer')":
							BTstate = 0
							client_socket.close()
							server_socket.close()
							print "Closed Bluettoth - disconnected"
						elif ex.args[0] == "(11, 'Resource temporarily unavailable')":
							# Ignore
							a = ex.args[0]
						else:
							print message
					else:
						print message

			else:
				print "Received: %s" % dataIn
         
				if (dataIn == 'q\n'):
					client_socket.close()
					server_socket.close()
					BTstate = 0
					isDataIn = False

			if isDataOut:
				print "Thread - attempt to send out data"
				client_socket.send(dataOut)
				isDataOut = False

# ----- end thread ---------


if LCDtype == 1:
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
elif LCDtype == 2:
	# Initialize library.
	disp.begin()

	# Clear display.
	disp.clear()
	disp.display()
	# Create blank image for drawing.
	# Make sure to create image with mode '1' for 1-bit color.
	width = disp.width
	height = disp.height
	image = Image.new('1', (width, height))

	# Draw some shapes.
	# First define some constants to allow easy resizing of shapes.
	padding = -2
	top = padding
	bottom = height-padding
	# Move left to right keeping track of the current x position for drawing shapes.
	x = 0

	# Load default font.
	font = ImageFont.load_default()
	# Get drawing object to draw on image.
	draw = ImageDraw.Draw(image)
	# Shell scripts for system monitoring from here : https://unix.stackexchange.com/questions/119126/command-to-display-memory-usage-disk-usage-and-cpu-load
	cmd = "hostname -I | cut -d\' \' -f1"
	IP = subprocess.check_output(cmd, shell = True )
	
	# Write two lines of text.
	draw.text((x, top),       "IP: " + str(IP),  font=font, fill=255)
#	draw.text((x, top+8),     str(CPU), font=font, fill=255)
#	draw.text((x, top+16),    str(MemUsage),  font=font, fill=255)
#	draw.text((x, top+25),    str(Disk),  font=font, fill=255)

	# Display image.
	disp.image(image)
	disp.display()


# Monitor push buttons
# The main loop of the program check if the Select button is pressed.
# If is pressed, the shutdown is issued

isDataIn = False
isDataOut = False

t1 = threading.Thread(target= waitBTthread, args=())

while True:
	if LCDtype == 1:
		# Check if Select is pressed
		if lcd.is_pressed(LCD.SELECT):
			# Button is pressed, change the message and backlight.
			lcd.clear()
			lcd.message('Shutdown\nin 5 sec.')
			time.sleep(5)
			lcd.clear()
			os.system("sudo poweroff")

		# Color display management
		if (BTstate == 0):
			lcd.set_color(1.0, 0.0, 0.0)
			lcd.clear()
			#lcd.message('Disconnected\nBluetooth')
			lcd.message('IP WLAN:\n')
			lcd.message(commands.getoutput('hostname -I'))
		elif (BTstate == 1):
			lcd.set_color(0.0, 1.0, 0.0)
		elif (BTstate == 2):
			lcd.set_color(0.0, 0.0, 1.0)
		else:
			lcd.set_color(0.0, 0.0, 0.0)
	elif LCDtype == 2:
		if (BTstate == 0):
			draw.text((x, top+8),  "Disconnected", font=font, fill=255)
		elif (BTstate == 2):
			draw.text((x, top+8),  "Connected   ", font=font, fill=255)
	        disp.image(image)
        	disp.display()

	# Bluetooth management
	if (BTstate == 0):
		# Set up Bluettoth
		# Restart Bluetooth and set for slave
		os.popen('sudo hciconfig hci0 reset')
		os.popen('sudo hciconfig hci0 piscan')

		print "Bluetooth initialization - set as slave"

		t1 = threading.Thread(target= waitBTthread, args=())
		if t1.is_alive() == False:
			print "Start thread  waiting for connection"
			t1.start()
#		BTstate = 1

#   if (BTstate == 1):
#      print "."

	if (BTstate == 2):
		# Check if received data
		if isDataIn:
			print "Main : %s" % dataIn
			if LCDtype == 1:
				lcd.clear()
        			lcd.message(dataIn)
			elif LCDtype == 2:
				draw.text((x, top+16),  dataIn, font=font, fill=255)
			        disp.image(image)
			        disp.display()
			isDataIn = False

		if LCDtype == 1:
			# Check if Down is pressed
			if lcd.is_pressed(LCD.DOWN):
				if isDataOut == False:
					# Button is pressed, send message
					print "Down button pressed - send message"
					dataOut = "Down\n"
					isDataOut = True
			if lcd.is_pressed(LCD.UP):
				if isDataOut == False:
					# Button is pressed, send message
					print "Up button pressed - send message"
					dataOut = "Up\n"
					isDataOut = True

