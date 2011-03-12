# -*- coding: utf-8 -*-
import cv

global capture, show
show = False
capture = None

def init(show_=False):
  global capture, show, camera_index
  if show_:
    cv.NamedWindow("w1", cv.CV_WINDOW_AUTOSIZE)
  show = show_
  camera_index = 0
  capture = cv.CaptureFromCAM(camera_index)

def repeat():
  global capture #declare as globals since we are assigning to them now
  global camera_index
  global show
  frame = cv.QueryFrame(capture)
  if show:
	cv.ShowImage("w1", frame)
  c = cv.WaitKey(50)
  if c>-1 and chr(c) =='q':
    print chr(c)
    return None
  return cv.EncodeImage(".jpeg", frame, [cv.CV_IMWRITE_JPEG_QUALITY, 50])

if __name__=='__main__':
  init(True)
  while repeat():
	continue
