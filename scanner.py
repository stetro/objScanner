#!/usr/bin/python2

# Author Steffen Troester

# -- USED LIBRARYS --

# libfrenect libraray (AUR for ArchLinux)
import freenect
# OpenCV (Open Source Computer Vision) is a library of programming 
# functions for real time computer vision 
import cv
# numpy for array calculations
import numpy
# sys library for argv
import sys

# Loopvariable
keep_running = True

# initialy calibrate tilt degs
if len(sys.argv) > 1:
	tilt_degs = float(sys.argv[1])
else:
	tilt_degs = 10
calibrate_tilt_degs = True

# clipping area
back_clipping = 200
inverted_depth = False

# Scrollhandler for back_clipping
def change_back_clipping(value):
	global back_clipping
	back_clipping = value

# taken photos
taken_photos = 0

# Create Window for Depthinformations with clipping chooser
depth_window_name = 'WPF Virtual Reality - Depth Information'
cv.NamedWindow(depth_window_name)
cv.CreateTrackbar('Background Clip Value', depth_window_name , back_clipping, 0xFF, change_back_clipping)

# loopdefinition for freenect
def body(*args):
	# use globals in context
	global calibrate_tilt_degs, tilt_degs
	
	# print(freenect.get_accel(args[0]))
	# if program has to calibrate tilt degs
	if calibrate_tilt_degs:
		# keep kinect on tilt_degs
		print("current tilt degrees changed to "+str(tilt_degs))
		freenect.set_tilt_degs(args[0],tilt_degs)		
		calibrate_tilt_degs = False
		
	# stop runloop if keep_running is false
	if not keep_running:
		# shutdown kinect features
		raise freenect.Kill

# open and display the cv window with depth information
# handles keyevents when the frame is rendered !
def display_depth(dev, data, timestamp):
	# convert data for cv window
	for_cv_converted_frame = convert_frame_for_cv(data)
	# display window
	cv.ShowImage(depth_window_name, for_cv_converted_frame)
	# key event
	keypressed = cv.WaitKey(10)
	handle_key_event(keypressed,data)
	

def handle_key_event(keypressed,data):
	# use globals in context
	global keep_running, inverted_depth, tilt_degs, calibrate_tilt_degs
	# keyrequest for ESC Key
	if keypressed == 27:
		keep_running = False
	if keypressed == 105:
		inverted_depth = not inverted_depth
		print("Invert Depth Information ...")
	# keyrequest for capuring
	if keypressed == 32:
		save_depth_information(data)
	# controll tilt
	if keypressed == 106:
		tilt_degs += 1
		calibrate_tilt_degs = True
	if keypressed == 107:
		tilt_degs -= 1
		calibrate_tilt_degs = True		

# convert the frame data for cv windows (depth)
def convert_frame_for_cv(data):
	# clip frame
	data = clip_and_prepare_frame(data)
	# create image with size and DEPTH
	image = cv.CreateImageHeader((data.shape[1], data.shape[0]), cv.IPL_DEPTH_8U, 1)
	# handle image
	cv.SetData(image, data.tostring(), data.dtype.itemsize * data.shape[1])
	return image
	

# prepare and clip the frame for storage or display
def clip_and_prepare_frame(data):
	# use globals in context
	global  back_clipping
	# shift elements for correct usage
	data >>= 1
	# convert to uint8 values (unsigned int with 1 byte)
	data = data.astype(numpy.uint8)	
	# !! MAGIC - clip data behind and before the object
	numpy.clip(data, 0, back_clipping, data)
	# invertienren
	if(inverted_depth):
		data *= -1
		
	# if(inverted_depth):
	# 	data += back_clipping
	# else:
	#	data -= back_clipping
	
	return data

# save depth information in file and analyse them
def save_depth_information(data):
	# use globals in context
	global back_clipping
	# debug	
	print("Frame will be analysed ...");
	# convert image
	depth_image = convert_frame_for_cv(data)
	# save image
	global taken_photos
	cv.SaveImage("depth-"+str(taken_photos)+".png", depth_image)
	taken_photos+=1
	print("Took photo in to depth-"+str(taken_photos)+".png !");


print('Press ESC in window to stop')
# start runloop
freenect.runloop(depth=display_depth, body=body)

