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
# for subprocessing view
import commands

# Loopvariable
keep_running = True

# initialy calibrate tilt degs
if len(sys.argv) > 1:
	tilt_degs = float(sys.argv[1])
else:
	tilt_degs = 20
calibrate_tilt_degs = True

# clipping area
back_clipping = 200
inverted_depth = False

# taken photos
taken_photos = 0

# depth data
depth_data = []


# Scrollhandler for back_clipping
def change_back_clipping(value):
	global back_clipping
	back_clipping = value


# Scrollhandler for tilt_degs
def change_tilt_degs(value):
	global tilt_degs, calibrate_tilt_degs
	tilt_degs=value-20
	calibrate_tilt_degs=True
	

# Create Window for Depthinformations with clipping chooser
depth_window_name = 'WPF Virtual Reality - Depth Information'
cv.NamedWindow(depth_window_name)
cv.CreateTrackbar('Background Clip Value', depth_window_name , back_clipping, 0xFF, change_back_clipping)
cv.CreateTrackbar('Tilt Degrees', depth_window_name, tilt_degs, 40, change_tilt_degs)


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
	# convert as array and clip
	data = clip_and_prepare_frame(data)
	# convert data for cv window
	for_cv_converted_frame = convert_frame_for_cv(data)
	# display window
	cv.ShowImage(depth_window_name, for_cv_converted_frame)
	# key event
	keypressed = cv.WaitKey(10)
	handle_key_event(keypressed,data,for_cv_converted_frame)


# capture video signal save if necessary
def display_rgb(dev, data, timestamp):
	# use globals in context
	global depth_data
	# save image to the depth information
	if len(depth_data) > 0  :
		save_rgb_information(data)
		save_3d_information(depth_data,data)
		depth_data = []
	

# handles key event of display_depth
def handle_key_event(keypressed,data,for_cv_converted_frame):
	# use globals in context
	global keep_running, inverted_depth, tilt_degs, calibrate_tilt_degs, depth_data
	# keyrequest for ESC Key
	if keypressed == 27:
		keep_running = False
	if keypressed == 105:
		inverted_depth = not inverted_depth
		print("Invert Depth Information ...")
	# keyrequest for capuring
	if keypressed == 32:
		depth_data = data
		save_depth_information(for_cv_converted_frame)


# convert the frame data for cv windows (depth)
def convert_frame_for_cv(data):
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
	
	# !! extract depth information from background!
	if(inverted_depth):
	 	data += back_clipping
	else:
		data -= back_clipping
	
	return data


# save depth information in file and analyse them
def save_depth_information(data):
	# use globals in context
	global taken_photos
	# save image
	taken_photos+=1
	cv.SaveImage("depth-"+str(taken_photos)+".png", data)
	print("Took photo in to depth-"+str(taken_photos)+".png !")


# save rgb information in file
def save_rgb_information(video):
	# use globals in context
	global taken_photo
	# convert image
	video = video[:, :, ::-1]
	rgb_image = cv.CreateImageHeader((video.shape[1], video.shape[0]),cv.IPL_DEPTH_8U,3)
	cv.SetData(rgb_image, video.tostring(),video.dtype.itemsize * 3 * video.shape[1])
	# save image
	cv.SaveImage("rgb-"+str(taken_photos)+".png", rgb_image)
	print("Took photo in to rgb-"+str(taken_photos)+".png !")


# save information in csv File
def save_3d_information(depth, video):
	# use globals in context
	global taken_photo
	# create pointcloud file
	pointcloud_file = open('pointcloud-'+str(taken_photos)+'.pcd','wb')
	
	index = 0
	print("start first analysing ...")
	# iterate through image information and save if necessary
	for y in range(0, 480):
		for x in range(0, 640):
			if depth[y][x] != 0:
				index += 1
		# state information (progressbar)
		percent = int(float(y) /float(480)*100)
		sys.stdout.write(str(percent).zfill(2)+" % - ")
		# output
		for i in range(0,int(percent/2)):
			sys.stdout.write("#")
		sys.stdout.write("\r")
		sys.stdout.flush()

	# PLY HEADER
	pointcloud_file.write("# .PCD v.7 - Point Cloud Data file format\n")
	pointcloud_file.write("VERSION .7\n")
	pointcloud_file.write("FIELDS x y z rgb\n")
	pointcloud_file.write("SIZE 4 4 4 4\n")
	pointcloud_file.write("TYPE F F F F\n")
	pointcloud_file.write("COUNT 1 1 1 1\n")
	pointcloud_file.write("WIDTH "+str(index)+"\n")
	pointcloud_file.write("HEIGHT 1\n")
	pointcloud_file.write("VIEWPOINT 0 0 0 1 0 0 0\n")
	pointcloud_file.write("POINTS "+str(index)+"\n")
	pointcloud_file.write("DATA ascii\n")

	depth -= numpy.argmin(depth)

	depthcalc = 2.0

	print("start second analysing ...")
	# iterate through image information and save if necessary
	for y in range(0, 480):
		for x in range(0, 640):
			if depth[y][x] != 0:
				pointcloud_file.write(str(float(x)/depthcalc)+" "+str(float(y)/depthcalc)+" "+str(depth[y][x])+" "+str(0)+"\n")
		# state information (progressbar)
		percent = int(float(y) /float(480)*100)
		sys.stdout.write(str(percent).zfill(2)+" % - ")
		# output
		for i in range(0,int(percent/2)):
			sys.stdout.write("#")
		sys.stdout.write("\r")
		sys.stdout.flush()
		
	pointcloud_file.close()



print('Press ESC in window to stop')
# start runloop
freenect.runloop(depth=display_depth,video=display_rgb, body=body)

