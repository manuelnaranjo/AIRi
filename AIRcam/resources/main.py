# -*- coding: utf-8 -*-
import sys, android, os, time
from protocol2 import Camera
from streamserver import StreamServer
from base64 import b64encode
from ffmpeg import ffmpeg

droid = android.Android()
running = True

global server, droid, init, camera, lastStop, ff
record_buffer = None
droid.makeToast("AIRcable AIRcam Loading....")
lastStop = None
ff = ffmpeg()

def exit():
    droid.bluetoothStop()
    sys.exit(0)

def disconnect():
    droid.bluetoothStop()

def connect():
    ret = droid.startActivityForResult('net.aircable.aircam.DeviceListActivity')
    if ret.error:
        droid.makeToast(ret.error)
        sys.exit(0)

    droid.makeToast("Connecting...")
    res = droid.bluetoothConnect("00001101-0000-1000-8000-00805F9B34FB", ret.result['extras']['device_address'])
    if not res.error:
	global camera
        droid.makeToast("Connected...")
        camera.handle_connect()
    else:
        droid.makeToast("Failed connecting try again")
    return res.error != None

def callback(frame):
    try:
	droid.log("got frame [%s bytes]" % len(frame))
	global server, init, record_buffer, ff
	server.send_to_all(frame, mimetype="image/jpeg")
	ff.push_frame(frame)
    except Exception,err:
	droid.log("%s" % err)

def error(*args, **kwargs):
    droid.log("error: %s, %s" % (args, kwargs))
    droid.bluetoothStop()
    droid.makeToast("Need to reconnect")
    sys.exit(0)

def record_start(fps=None, path=None):
    global ff
    ff.start_recording(fps=fps, path=path)

def record_stop():
    global ff
    ff.stop_recording()

def handleEvent(event):
    name = event.result['name'];
    data = event.result['data'];

    if data == 'exit':
	exit()
    elif data == 'connect':
	connect()
    elif data == 'disconnect':
	disconnect()
    elif data == 'onpause':
	global lastStop
	droid.log("GUI has gone onPause")
	lastStop = time.time()
    elif data == 'onresume':
	global lastStop
	lastStop = None
    elif data.startswith('record_start'):
	record_start(data.split('$')[1])
    elif data == 'record_stop':
	record_stop()
    else:
	droid.log("Not known event %s" % data)

server=StreamServer('', 10000, droid)
server.create_server_socket()

init = True

droid.toggleBluetoothState(True)

camera = Camera(droid, size="QQVGA", callback=callback, err_callback=error)
connect()
droid.startActivity('de.mjpegsample.MjpegSample')

while running:
    server.wait_connection()
    try:
	if len(droid.bluetoothActiveConnections().result)>0:
          if droid.bluetoothReadReady():
            camera.handle_read()
        else:
    	    server.killChildrens()
    except:
      pass
    event = droid.receiveEvent() 
    if event.result:
	handleEvent(event)
    if lastStop and time.time() - lastStop > 3*60:
	lastStop = None
	droid.log("client has been down for too long, we disconnect")
	disconnect()
    time.sleep(0.001);
