# -*- coding: utf-8 -*-
from twisted.python import log
from twisted.internet import reactor
from airi.camera import dbg, CameraProtocol
from airi.settings import getSettings

settings=getSettings()

SIZES={
  #day modes
  "QVGA":	1,
  "VGA": 2,
  "XGA": 3,
  "720P": 6,
  "QXGA": 5,

  "QVGA Zoom 1": 11,
  "QVGA Zoom 2": 12,
  "QVGA Zoom 3": 13,
}

PANS = [ "none", "right", "left", "up", "down" ]

CAPABILITIES={ 
  'size':       SIZES.keys(),
  'flash':      True,
  'pan':        PANS,
  'voice':      False, # by now ;)
  'exposure':   True,
  'transport':  ['RFCOMM', 'L2CAP'],
  'battery':    True,
}

class AIRi(CameraProtocol):
  client = None
  callLater = None
  size = "QVGA"
  defaults = {
    "size": "QVGA",
    "flash": 0,
    "voice": False,
    "exposure": 0,
    "pan": "none",
  }

  def getType(self):
    return 'AIRi'

  def __init__(self, client):
    self.client = client
    self.address = client.address
    self.transport = client.transport
    self.doSetup()
  
  def __doCommand(self, command, value):
    dbg("doCommand %s %s" % (command, value))
    self.transport.write("$%s%s\n" % (command, value))

  def doSetup(self):
    dbg("doSetup")
    nsets = settings.getCamera(self.address)
    sets = self.defaults
    size = self.size
    if nsets:
      sets.update(nsets)
    dbg(sets)
    self.doCommand("S", SIZES[sets["size"]])
    self.doCommand("F", "0" if not sets["flash"] else "1")
    if sets["pan"]!="none":
      self.doCommand("P", sets["pan"])
    self.doCommand("E", sets["exposure"])

  def updateSettings(self):
    self.doSetup()

  def doCommandMode(self):
    dbg("doCommandMode")
    self.state = COMMAND_MODE
    self.__doCommand(1)
    self.callLater = reactor.callLater(1, self.doSetSize)

  def previewData(self):
    start = self.client.buffer.find("\xff\xd8")
    end = self.client.buffer.find("\xff\xd9")
    if start == -1 or end == -1:
      return

    frame = self.client.buffer[start:end+1]
    self.client.buffer = self.client.buffer[end+2:]
    self.client.gotFrame(frame)

  def dataReceived(self):
    return self.previewData()

  def disconnect(self):
    dbg("AIRi.disconnect")

AIRi.Capabilities = CAPABILITIES
AIRi.Sizes = SIZES
AIRi.Panning = PANS
