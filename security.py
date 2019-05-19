# Commands to move the Tenvis cameras
#PTZ_STOP=1
#TILT_UP=0
#TILT_UP_STOP=1
#TILT_DOWN=2
#TILT_DOWN_STOP=3
#PAN_LEFT=4
#PAN_LEFT_STOP=5
#PAN_RIGHT=6
#PAN_RIGHT_STOP=7
#PTZ_LEFT_UP=90
#PTZ_RIGHT_UP=91
#PTZ_LEFT_DOWN=92
#PTZ_RIGHT_DOWN=93
#PTZ_CENTER=25
#PTZ_VPATROL=26
#PTZ_VPATROL_STOP=27
#PTZ_HPATROL=28
#PTZ_HPATROL_STOP=29

import numpy as np
import cv2
import sqlite3
import urllib
import time
import os
from Tkinter import *


def runCamera(cameraName):
	try:	
		motionDetectedTimestamp = ""

		# Connect to database
		conn = sqlite3.connect('opencv_database.db')
		c = conn.cursor()

		# Get camera values from database
		ip = retrieveFromDatabase("ip", cameraName)
		port = retrieveFromDatabase("port", cameraName)
		password = retrieveFromDatabase("password", cameraName)

		# Create camera url
		mpegURL = "http://" + ip + ":" + port + "/videostream.asf?user=admin&pwd=" + password + "&resolution=32&rate=0&.mpg"

		# Specify the video to be captured
		cap = cv2.VideoCapture(mpegURL)

		# Get the starting time and starting video number
		startTime = time.time()
		videoNumber = 1

		# Codec and VideoWriter object for saving the video
		fileSaveDirectory = retrieveDirectoryFromDB()
		fourcc = cv2.cv.CV_FOURCC(*'XVID')
		out = getOutputFile(fileSaveDirectory, videoNumber, fourcc) 

		fgbg = cv2.BackgroundSubtractorMOG()

		motionDetectedFrameCount = 0
		motionDetected = False
		mute = True
		# While the camera is recording
		while(True):
			# Check for any keys that were pressed
			k = cv2.waitKey(30) & 0xff
			if k == ord('q') or k == 27:
				break
			elif k == ord('k'):
				# Generate a new background
				fgbg = cv2.BackgroundSubtractorMOG()
			elif k == ord('m'):
				mute = not mute 
			elif k == ord('w'):
				# Move camera up
				moveCamera(password, ip, port, 0)
			elif k == ord('a'):
				# Move camera left
				moveCamera(password, ip, port, 4)
			elif k == ord('s'):
				# Move camera down
				moveCamera(password, ip, port, 2)
			elif k == ord('d'):
				# Move camera right	
				moveCamera(password, ip, port, 6)
			# Stop any camera movement
			moveCamera(password, ip, port, 1)

			# Read the current frame from the camera
			ret, frame = cap.read()

			# If there has been motion detected for more than a specified number of frames, generate a new mask
			if motionDetectedFrameCount > 1:
				fgbg = cv2.BackgroundSubtractorMOG()
				motionDetectedFrameCount = 0

			# Apply the mask to the frame
			fgmask = fgbg.apply(frame)
			kernel = np.ones((5,5),np.uint8)	
			fgmask = cv2.erode(fgmask,kernel,iterations = 1)
			fgmask = cv2.dilate(fgmask,kernel,iterations = 4)
			
			# Find differences between the mask and frame, if any.  These are called contours
			contours, hierarchy = cv2.findContours(fgmask,cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE)

			# If there are no contours an error will be thrown.  If there are contours:
			if len(contours) != 0:
				motionDetectedFrameCount += 1
				motionDetected = True
				cnt = contours[0]
				x,y,w,h = cv2.boundingRect(cnt)
				minX = x
				minY = y
				maxX = x + w
				maxY = y + h
				for contour in contours:
					x,y,w,h = cv2.boundingRect(contour)
					if x < minX:
						minX = x
					elif y < minY:
						minY = y
					elif (x + w) > maxX:
						maxX = (x + w)
					elif (y + h) > maxY:
						maxY = (y + h)
				# Draw a target around the motion detected
				centerX = (minX + maxX) / 2
				centerY = (minY + maxY) / 2
				cv2.rectangle(frame,(centerX,centerY),(centerX,centerY),(255,000,255),2)
				cv2.rectangle(frame,(minX,minY),(maxX,maxY),(255,000,255),2)
				# Play a sound to alert the user of motion detected
				if not mute:
					os.system("aplay beep.wav")

				# Record movement time of occurrence in log
				#if (motionDetectedTimestamp != time.asctime(time.localtime())):
				#	motionDetectedTimestamp = time.asctime(time.localtime())
				#	logTimestamp()
		
			# Put text over video frame
			# Put a timestamp on the video frame
			font = cv2.FONT_HERSHEY_SIMPLEX
			cv2.putText(frame,str(time.asctime(time.localtime())),(0,25), font, 1, (0,0,0), 7)
			cv2.putText(frame,str(time.asctime(time.localtime())),(0,25), font, 1, (255,255,255), 2)
			# Add MUTE text if the program is muted
			if mute:
				cv2.putText(frame,"MUTE",(555,475), font, 1, (0,0,255), 4)

			# Show the frame, and write it to the .avi file
			cv2.imshow('Video',frame)
			out.write(frame)

			# Find how long the routine has been running for
			endTime = time.time() 
			elapsedTime = endTime - startTime

			# Save the video after a specified number of seconds
			if elapsedTime >= 4:
				out.release()
				# If there was motion detected during the recording, move on to the next video number.  Otherwise write over this video
				# If there are more than a specified number of videos, the count is set back to 1 so they can all be written over
				if (videoNumber == 2000) and (motionDetected == True):
					motionDetected = False
					videoNumber = 1
				elif motionDetected == True:
					motionDetected = False
					videoNumber += 1

				out = getOutputFile(fileSaveDirectory, videoNumber, fourcc); 
				startTime = time.time()
		cap.release()
		out.release()
		cv2.destroyWindow('Video')
	except:
		pass

def getOutputFile(fileSaveDirectory, videoNumber, fourcc):
	outputFile = cv2.VideoWriter(str(fileSaveDirectory) + str(videoNumber) + '.avi',fourcc, 12, (640,480))
	return outputFile

def logTimestamp():
	queryText = 'INSERT INTO log (timestamp) VALUES ("' + time.asctime(time.localtime()) + '");'
	c.execute(queryText)
	conn.commit()

def retrieveFromDatabase(value, camera):
	# Get value from database
	queryText = 'SELECT ' + value + ' FROM cameras WHERE name = "' + camera + '";'
	result = c.execute(queryText)
	# Strip extra characters from the query result
	for value in result:
		value = str(value)
		value = value[3:len(value)-3]
	return value

def retrieveDirectoryFromDB():
	# Get value from database
	queryText = 'SELECT directory FROM save_directory;'
	result = c.execute(queryText)
	# Strip extra characters from the query result
	for value in result:
		value = str(value)
		value = value[3:len(value)-3]
	return value
	
def moveCamera(password, ip, port, direction):
	direction = str(direction)
	moveURL = "http://admin:" + password + "@" + ip + ":" + port + "/decoder_control.cgi?command=" + direction + ""
	urllib.urlopen(moveURL)

class MyApp:
	def __init__(self, parent):
		self.frame = Frame(parent)
		self.frame.pack()
		self.home()

	def home(self):
		# Remove all widgets from the frame
		self.clearFrame()
		rowCount = 0
	
		# Get any existing cameras from the database
		cameras = c.execute('SELECT name FROM cameras;')
		for camera in cameras:
			camera = str(camera)
			camera = camera[3:len(camera)-3]
			# Add widgets for the camera
			newCameraButton = Button(self.frame, text="" + camera + "", command = lambda name=camera:self.startCameraFeed("" + name  + ""))
			newRemoveButton = Button(self.frame, text="Remove", command = lambda name=camera:self.removeCamera("" + name + ""))
			# Position the widgets
			newCameraButton.grid(row=rowCount, sticky=E)
			newRemoveButton.grid(row=rowCount, column=1)
			rowCount += 1
			
		# Add default widgets to the frame
		self.addCameraButton = Button(self.frame, text="Add Camera", command=self.addCamera)
		self.settingsButton = Button(self.frame, text="Settings", command=self.settings)
		self.quitButton = Button(self.frame, text="Quit", command=self.closeWindow)

		# Position the default widgets
		self.addCameraButton.grid(row=rowCount, columnspan=2)
		self.settingsButton.grid(row=rowCount + 1, columnspan=2)	
		self.quitButton.grid(row=rowCount + 2, columnspan=2)

	def addCamera(self):
		# Remove all widgets from the frame
		self.clearFrame()

		# Add new widgets to the frame
		self.nameLabel = Label(self.frame, text="Camera name:") 
		self.ipLabel = Label(self.frame, text="IP address:")
		self.portLabel = Label(self.frame, text="Port:")
		self.passwordLabel = Label(self.frame, text="Password:")
		self.modelLabel = Label(self.frame, text="Model:")
		self.nameEntry = Entry(self.frame)
		self.ipEntry = Entry(self.frame)
		self.portEntry = Entry(self.frame)
		self.passwordEntry = Entry(self.frame)
		self.modelEntry = Entry(self.frame)
		self.addCameraButton = Button(self.frame, text="Add", command=self.writeCameraToDatabase)
		self.backButton = Button(self.frame, text="Back", command=self.home)
		
		# Position the widgets
		self.nameLabel.grid(row=0, sticky=E) 
		self.ipLabel.grid(row=1, sticky=E)
		self.portLabel.grid(row=2, sticky=E)
		self.passwordLabel.grid(row=3, sticky=E)
		self.modelLabel.grid(row=4, sticky=E)
		self.nameEntry.grid(row=0, column=1)
		self.ipEntry.grid(row=1, column=1)
		self.portEntry.grid(row=2, column=1)
		self.passwordEntry.grid(row=3, column=1)
		self.modelEntry.grid(row=4, column=1)	
		self.addCameraButton.grid(row=5, columnspan=2)
		self.backButton.grid(row=6, columnspan=2)

	def settings(self):
		# Remove all widgets from the frame
		self.clearFrame()

		result = c.execute('SELECT directory FROM save_directory;')
		for directory in result:
			directory = str(directory)
			directory = directory[3:len(directory)-3]
			 
		# Add new widgets to the frame
		self.saveDirectoryLabel = Label(self.frame, text="Save directory:")
		self.saveDirectoryEntry = Entry(self.frame)
		self.saveDirectoryEntry.insert(0, "" + directory + "")
		self.saveButton = Button(self.frame, text="Save", command=self.writeDirectoryToDatabase)
		self.backButton = Button(self.frame, text="Back", command=self.home)

		# Position the widgets
		self.saveDirectoryLabel.grid(row=0, sticky=E)
		self.saveDirectoryEntry.grid(row=0, column=1)
		self.saveButton.grid(row=1, columnspan=2)
		self.backButton.grid(row=2, columnspan=2)

	def clearFrame(self):
		for widget in self.frame.winfo_children():
			widget.destroy()

	def writeCameraToDatabase(self):
		name = self.nameEntry.get()
		ip = self.ipEntry.get()
		port = self.portEntry.get()
		password = self.passwordEntry.get()
		model = self.modelEntry.get()
	
		c.execute('INSERT INTO cameras (name, ip, port, password, model) VALUES ("' + name + '", "' + ip + '", "' + port + '", "' + password + '", "' + model + '");')
		conn.commit()
		self.home()

	def writeDirectoryToDatabase(self):
		directory = self.saveDirectoryEntry.get()
		if (directory[len(directory) - 1] != "/"):
			directory += "/"
		c.execute('DELETE FROM save_directory')
		c.execute('INSERT INTO save_directory (directory) VALUES ("' + directory + '");')
		conn.commit()
		self.home()
				
	def removeCamera(self, name):
		c.execute('DELETE FROM cameras WHERE name = "' + name + '";')
		conn.commit()
		self.home()
	
	def startCameraFeed(self, name):
		runCamera(name)
		self.closeWindow()
	
	def closeWindow(self):
		root.destroy()

# Connect to database
conn = sqlite3.connect('opencv_database.db')
c = conn.cursor()

root = Tk()
root.title("security.py")
root.minsize(width=640, height=480)
myApp = MyApp(root)
root.mainloop()
