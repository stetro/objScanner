#!/usr/bin/python2

import freenect
import cv
import numpy

keep_running = True
cv.NamedWindow("POINT")
cv.NamedWindow("PAINT")
painter = cv.CreateImage((640, 480), cv.IPL_DEPTH_8U,3)

x = [0,0,0,0]
y = [0,0,0,0]
xpos =0
ypos =0


def display_depth(dev, data, timestamp):
	global painter
	frame = prepare_frame(data)
	image = prepare_for_cv(frame)
	cv.ShowImage("POINT",image)
	cv.ShowImage("PAINT",painter)
	keypressed = cv.WaitKey(10)
	if keypressed == 27:
		global keep_running
		keep_running=False

def prepare_for_cv(data):
	global x,y,painter
	image = cv.CreateImageHeader((data.shape[1], data.shape[0]), cv.IPL_DEPTH_8U,1)
	cv.SetData(image,data.tostring(),data.dtype.itemsize * data.shape[1])
	nx = int(numpy.median(x))
	ny = int(numpy.median(y))
	cv.Circle(image,(nx,ny),5,cv.Scalar(0xFF,0xFF,0xFF),3)
	cv.Line(painter,(nx,ny),(nx,ny),cv.Scalar(0x00,0,0xFF),2)
	return image

def prepare_frame(data):
	global x,y,xpos,ypos

	data >>=2
	data = data.astype(numpy.uint8)
	data *=-1
	data += 5
	
	pos = numpy.argmax(data)

	xpos = (xpos + 1) % len(x)
	ypos = (xpos + 1) % len(y)

	x[xpos] = pos % data.shape[1]
	y[ypos] = pos / data.shape[1]

	return data

def body(*args):
	if not keep_running:
		raise freenect.Kill
	
freenect.runloop(depth=display_depth,body=body)
