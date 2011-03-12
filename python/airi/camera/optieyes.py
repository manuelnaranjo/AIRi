# -*- coding: utf-8 -*-
from twisted.python import log
from twisted.internet import reactor
from airi.camera import dbg, CameraProtocol
from airi.settings import getSettings

settings=getSettings()

SIZES={
    "VGA":	4,
    "QVGA":	5,
    "QQVGA":6,
    "SVGA":	0xc,
    "XVGA":	0xd,
}

CAPABILITIES={ 
  'size':       SIZES.keys(),
  'pan':        [],
  'flash':      False,
  'voice':      False,
  'exposure':   False,
  'transport':  ['RFCOMM',],
  'battery':    False,
}

IDLE=0
ECHO=1
PREVIEW=2
COMMAND_MODE=3

class OptiEye(CameraProtocol):
  client = None
  state = IDLE
  callLater = None
  size = "QVGA"

  def getType(self):
    return 'OptiEye'

  def getCapabilities(self):
    return CAPABILITIES

  def getTransport(self):
    return "RFCOMM"

  def __init__(self, client):
    self.client = client
    self.address = client.address
    self.transport = client.transport
    self.doCommandMode()

  def setSize(self, size):
    if size not in SIZES:
      raise RuntimeException("Size not valid")
    self.size = size

  def getSize(self):
    return self.size

  def getSizes(self):
    return SIZES

  def __doCommand(self, command):
    self.transport.write("$GENIESYS%04X\r\n" % command)

  def updateSettings(self):
    self.doCommandMode()

  def doCommandMode(self):
    dbg("doCommandMode")
    self.state = COMMAND_MODE
    self.__doCommand(1)
    self.callLater = reactor.callLater(1, self.doSetSize)

  def doSetSize(self):
    self.state = ECHO
    self.callLater = None
    camera=settings.getCamera(self.address)
    size = "QVGA" #default
    if camera:
      size = camera.get("size", size)
    dbg("doSetSize(%s)", size)
    self.__doCommand(SIZES[size])
    self.callLater = reactor.callLater(1, self.doPreview)

  def doPreview(self):
    dbg("doPreview")
    self.state = PREVIEW
    self.callLater = None
    self.__doCommand(2)

  def previewData(self):
    #dbg("previewData")
    start = self.client.buffer.find("\xff\xd8")
    end = self.client.buffer.find("\xff\xd9")
    #dbg("start: %s, end: %s" % ( start, end ))
    if start == -1 or end == -1:
      return

    frame = self.client.buffer[start:end+1]
    self.client.buffer = self.client.buffer[end+2:]
    self.client.gotFrame(frame)

  def dataReceived(self):
    #dbg("OptiEye.dataReceived, have %s bytes" % len(self.client.buffer))
    #dbg("state = %s" % self.state)

    if self.state == COMMAND_MODE:
      self.callLater.reset(1) # wait another second
      #dbg("Dropping %s" % self.client.buffer)
      self.client.buffer = ""
      return

    if self.state == PREVIEW:
      return self.previewData()

  def set(self, option, value):
    dbg("set %s->%s", option, value)

  def disconnect(self):
    dbg("OptiEyes.disconnect")
    self.__doCommand(1)

OptiEye.Capabilities = CAPABILITIES
OptiEye.Sizes = SIZES
OptiEye.Panning = None
