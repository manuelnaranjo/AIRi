# -*- coding: utf-8 -*-
'''
Created on 20/09/2010

@author: manuel
'''

import time, re, asyncore, struct, codecs
from functools import partial
from base64 import b64decode

import logging 
logging.basicConfig()
logging.logMultiprocessing=False
logger=logging.getLogger('AIRcam')
logger.setLevel(logging.DEBUG)


class FSM():
    NOTHING, \
    CONNECTING, \
    WELCOME, \
    SETUP, \
    IDLE, \
    STREAM, \
    ERROR, \
    COMMAND_MODE = range(8)

COMMAND_LINE="$GENIESYS%04X\r\n"
CAPTURE_SIZE=re.compile("\$SZE\s*(?P<size>\d+)")

COMMANDS=[
    'COMMAND_ECHO',
    'SET_COMMAND_MODE',
    'SET_PREVIEW_MODE',
    'CAPTURE_COMMAND',
    'SET_CAPTURE_VGA',
    'SET_CAPTURE_QVGA',
    'SET_CAPTURE_QQVGA',
    'GET_VERSION',
    'GET_CAPTURE_SIZE',
    'START_CAPTURE_SEND',
    'SET_RAW_REGISTER',
    'GET_RAW_REGISTER',
    'SET_CAPTURE_SVGA',
    'SET_CAPTURE_XVGA',
    'READ_EEPROM',
    'WRITE_EEPROM',
    'RESET_COMMAND'
]

SIZES = {
    'VGA': 'SET_CAPTURE_VGA',
    'QVGA': 'SET_CAPTURE_QVGA',
    'QQVGA': 'SET_CAPTURE_QQVGA',
    'SVGA': 'SET_CAPTURE_SVGA',
    'XVGA': 'SET_CAPTURE_XVGA',
}

JPG_START=chr(0xff)+chr(0xD8)
JPG_END  =chr(0xff)+chr(0xD9)
def find_jpeg(buffer):
    start = buffer.find(JPG_START)
    end = buffer.find(JPG_END, start)
    return start, end

def isascii(buffer):
    try:
        buffer.decode('ascii')
        print "ascii"
        return True
    except:
        return False

class Camera(asyncore.dispatcher):
    last_time = None

    def __init__(self, droid, size=None, callback=lambda x: None, err_callback=lambda x: None):
        asyncore.dispatcher.__init__(self)
        self.size=size or 'QQVGA'
        self.callback=callback 
        self.err_callback = err_callback
        self.state = FSM.IDLE
        self.buffer = ''
        self.droid=droid

    def recv(self, size=4096):
        result = self.droid.bluetoothReadBinary(size)
        if result.error==None:
            return b64decode(result[1])
        raise Exception("recv failed: %s" % result)

    def send(self, content):
        return self.droid.bluetoothWrite(content)

    def connect(self, *args, **kwargs):
        self.state = FSM.CONNECTING
        asyncore.dispatcher.connect(self, *args, **kwargs)

    def handle_connect(self):
        # gets called as soon as we get connected, or when
        # we are waiting for the camera to leave the stream mode
        # or the error state
        logger.info("handle_connect")
        self.state = FSM.WELCOME
        try:
            print self.recv(4096)
        except Exception, err:
            print err
        logger.info("connect done")
        
    def handle_read(self):
        self.buffer+=self.recv(4096) 

        start, end = find_jpeg(self.buffer)
        ready = start > -1 and end > -1 
        if not ready:
            if isascii(self.buffer):
                logger.debug(self.buffer)
            return

        self.callback(self.buffer[start:end+2])
        self.buffer = self.buffer[end+2:]

    def handle_close(self):
        logger.info("handle close")
        try:
    	    self.close()
    	except: # if we're running in a non asyncore compatible environment 
    		# like SL4A then this is likely to happen!
    	    pass
        self.err_callback(self)
    
    def do_delay(self):
        if self.last_time and time.time() - self.last_time < 3:
            logger.info("Waiting for 3 seconds")
            return True
        self.last_time = time.time()
        return False

    def do_error(self):
        # once we get into this state the only way to go on
        # is reseting the chip, an ACK0000 will tell us 
        # when the chip is ready again
        logger.debug(self.buffer)
        if self.do_delay():
            return
        self.state = FSM.ERROR
        self.buffer = ""

