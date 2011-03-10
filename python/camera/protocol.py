# -*- coding: utf-8 -*-
from twisted.internet.protocol import Protocol, ClientFactory
import twisted_bluetooth
from twisted.python import log
from camera import dbg, Listener
from twisted.internet import reactor
import optieyes
from functools import partial
import bluetooth
from settings import getSettings
from time import localtime, strftime
settings = getSettings()

TYPES = {
  'OPTIEYE': {
      "welcome": "genie cam on",
      "class": optieyes.OptiEye
  },
  'AIRI': {
      "welcome": "$airi",
  }
}

def getTagByType(tag):
  out = {}
  for k in TYPES:
    out[k] = TYPES[k][tag]
  return out

WELCOME = getTagByType("welcome")

INIT = 0
IDLE = 1

class Camera(Protocol):
  kind = None
  state = INIT
  callLater = None
  transport = None

  def __init__(self, address):  
    dbg("new camera instance for (%s)", address)
    setattr(self, "client", None)
    setattr(self, "buffer", "")
    self.address = address

  def invalidCamera(self):
    log.msg("not known camera, we stop")
    self.transport.loseConnection()

  def doINIT(self):
    dbg("doINIT", self.buffer)
    if self.buffer.find("\n") == -1:
      dbg("Welcome not received")
      if not self.callLater:
        self.callLater = reactor.callLater(3, self.invalidCamera)
      self.callLater.reset(2)
      return
    welcome, temp = self.buffer.split("\n", 1)
    welcome=welcome.strip().lower().strip('\x00')
    log.msg("welcome", welcome)

    kind = None
    for k,v in WELCOME.iteritems():
      if welcome.find(v) > -1:
        kind = k
        break;

    if not kind:
      if not self.callLater:
        self.callLater = reactor.callLater(3, self.invalidCamera)
      self.callLater.reset(2)
      return

    self.kind = kind
    log.msg("Connected to a %s camera" % self.kind)
    self.buffer=temp
    self.state=IDLE
    settings.setCamera(self.address, "address", self.address)
    settings.setCamera(self.address, "type", self.kind)
    settings.setCamera(self.address, "last", strftime("%m/%d/%Y %H:%M:%S", localtime())
    settings.save()
    self.client=TYPES[self.kind]["class"](self)
    if self.callLater:
      self.callLater.cancel()
      self.callLater = None

  def dataReceived(self, data):
    #dbg("dataReceived(%s)" % len(data))
    self.buffer += data
    if self.state == INIT:
      return self.doINIT()
    elif self.client:
      return self.client.dataReceived()

  def getName(self):
    return bluetooth.lookup_name(self.address)

  def __getattr__(self, val):
    dbg("__getattr__ %s" % val)
    if val in [
      'getType', 'getCapabilities', 'getSize', 'getFlash', 'getBattery',
        'getTransport', 'getExposure', 'getZoom', 'getPan', 'getVoice']:
        return getattr(self.client, val, lambda: False)
    raise AttributeError

class CameraFactory(ClientFactory):
  FACTORY = None
  clients = {}
  listeners = {}

  def startedConnecting(self, connector):
    log.msg("Started to connect.")

  def buildProtocol(self, addr):
    log.msg("Connected %s" % str(addr))
    CameraFactory.clients[addr[0]] = Camera(addr[0])
    CameraFactory.clients[addr[0]].gotFrame = partial(CameraFactory.gotFrame, addr[0])
    return CameraFactory.clients[addr[0]]

  @classmethod
  def gotFrame(klass, addr, frame):
    dbg("gotFrame %s" % addr)
    if addr not in klass.listeners:
      return
    for listener in klass.listeners[addr]:
      listener.gotFrame(frame, address=addr)

  @classmethod
  def setSize(klass, addr, size):
    klass.clients[addr].client.setSize(size)

  @classmethod
  def getSize(klass, addr):
    return klass.clients[addr].client.getSize()

  @classmethod
  def getSizes(klass, addr):
    return klass.clients[addr].client.getSizes()

  @classmethod
  def __cleanup(klass, addr):
    dbg("__cleanup(%s)" % addr)
    if addr in klass.listeners:
      del klass.listeners[addr]
    if addr in klass.clients:
      del klass.clients[addr].client
      del klass.clients[addr]

  def __lostConnection(self, addr, reason, failed):
    rep = False
    if addr in CameraFactory.listeners:
      for listener in CameraFactory.listeners[addr]:
        rep = rep or listener.lostConnection(reason, failed, address=addr)

      if not rep:
        CameraFactory.__cleanup(addr)

    if __name__=='__main__' and reactor.running:
      reactor.stop()

  def clientConnectionLost(self, connector, reason):
    addr = connector.getDestination()[0]
    log.msg("Lost connection to %s. Reason: %s" % (addr, reason))
    self.__lostConnection(addr, reason, False)

  def clientConnectionFailed(self, connector, reason):
    addr = connector.getDestination()[0]
    log.msg("Connection Failed to %s. Reason: %s" % (addr, reason))
    self.__lostConnection(addr, reason, True)

  @classmethod
  def isConnected(klass, addr):
    return addr in klass.clients

  @classmethod
  def connect(klass, address, channel, method="RFCOMM"):
    if klass.isConnected(address):
      raise RuntimeException("All ready connected to %s" % address)

    c = getattr(twisted_bluetooth, "connect%s" % method)

    if klass.FACTORY == None:
      klass.FACTORY=klass()
    c(reactor, address, channel, klass.FACTORY)


  @classmethod
  def disconnect(klass, address):
    if klass.isConnected(addresS):
      klass.clients[address].client.disconnect()
      klass.clients[address].transport.loseConnection()

    for listener in klass.listeners[address]:
      listener.forcedDisconnect(address=address)

    klass.__cleanup(address)

  @classmethod
  def registerListener(klass, address, listener):
    if not address in klass.listeners:
      klass.listeners[address] = list()
    klass.listeners[address].append(listener)

  @classmethod
  def removeListener(klass, address, listener):
    klass.listeners[address].remove(listener)

  @classmethod
  def getConnected(klass, address=None):
    if address:
      return klass.clients.get(str(address.strip()), None)
    return klass.clients

  @classmethod
  def getCamera(klass, address):
    out = settings.getCamera(address)
    out["status"]=klass.isConnected(address)
    if "type" in out:
      
    return settings.getCamera(address)

if __name__=='__main__':
  import sys
  class TestListener(Listener):
    def lostConnection(self, reason, failed):
      return False

    def gotFrame(self, frame, *a, **kw):
      print "got frame %s bytes long" % len(frame)
      CameraFactory.disconnect(sys.argv[1])

  if len(sys.argv) != 3:
    print "Usage %s <target> <channel>" % sys.argv[0]
    sys.exit(1)

  log.startLogging(sys.stdout)
  CameraFactory.connect(sys.argv[1], int(sys.argv[2]))
  CameraFactory.registerListener(sys.argv[1], TestListener())
  reactor.run()
