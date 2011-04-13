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
    dbg("doCommand $%s%s" % (command, value))
    self.transport.write("$%s%s\n\r" % (command, value))
    self.transport.flush()

  def doSetup(self):
    dbg("doSetup")
    nsets = settings.getCamera(self.address)
    sets = self.defaults
    size = self.size
    if nsets:
      sets.update(nsets)
    dbg(sets)
    self.__doCommand("S", SIZES[sets["size"]])
    self.__doCommand("F", "0" if not sets["flash"] else "1")
    if sets["pan"]!="none":
      self.__doCommand("P", sets["pan"])
    self.__doCommand("E", sets["exposure"])

  def updateSettings(self):
    self.doSetup()

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

  def set(self, option, value):
    dbg("set %s-> %s" % (option, value))
    if option == "size":
      self.__doCommand("S", SIZES[value])
    elif option == "flash":
      self.__doCommand("F", "0" if not value else "1")
    elif option == "pan":
      self.__doCommand("P", value)
    elif option == "exposure":
      self.__doCommand("E", value)

AIRi.Capabilities = CAPABILITIES
AIRi.Sizes = SIZES
AIRi.Panning = PANS
