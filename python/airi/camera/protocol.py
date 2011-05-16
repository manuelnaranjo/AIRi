# -*- coding: utf-8 -*-
from twisted.internet.protocol import Protocol, ClientFactory
import airi.twisted_bluetooth as twisted_bluetooth
from twisted.python import log
from airi.camera import dbg, Listener, UnknownDevice
from twisted.internet import reactor
import optieyes
import airicamera
from functools import partial
from airi.settings import getSettings
from airi import report
from time import localtime, strftime
settings = getSettings()


CATEGORY = "airi.camera.protocol"

TYPES = {
  'OPTIEYE': {
      "welcome": "genie cam on",
      "class": optieyes.OptiEye},
  'AIRI': {
      "welcome": "$airi",
      "class": airicamera.AIRi},
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

        def welcomeCheck():
            while len(self.buffer) > 0 and self.buffer.find('\n') > -1:
                welcome, self.buffer = self.buffer.split('\n', 1)
                dbg("welcome", welcome)
                welcome = welcome.strip().lower().strip('\x00')
                for k, v in WELCOME.iteritems():
                    if welcome.find(v) > -1:
                        return k

        dbg("doINIT", self.buffer)
        if self.buffer.find("\n") == -1:
            dbg("Welcome not received")
            if not self.callLater:
                self.callLater = reactor.callLater(3, self.invalidCamera)
            self.callLater.reset(2)
            return

        kind = welcomeCheck()
        if not kind:
            if not self.callLater:
                self.callLater = reactor.callLater(3, self.invalidCamera)
            self.callLater.reset(2)
            return

        self.kind = kind
        log.msg("Connected to a %s camera" % self.kind)
        dbg("still in buffer", len(self.buffer))
        self.state = IDLE
        settings.setCameraSetting(self.address, "address", self.address)
        settings.setCameraSetting(self.address, "type", self.kind)
        settings.setCameraSetting(self.address, "name", "NN")
        settings.setCameraSetting(self.address, "last",
                                    strftime("%m/%d/%Y %H:%M:%S", localtime()))
        settings.save()
        self.client = TYPES[self.kind]["class"](self)
        if self.callLater:
            self.callLater.cancel()
            self.callLater = None

    def dataReceived(self, data):
        self.buffer += data
        if self.state == INIT:
            return self.doINIT()
        elif self.client:
            return self.client.dataReceived()

    def __getattr__(self, val):
        if val in [
              'getType', 'getCapabilities', 'getSize', 'getFlash',
              'getBattery', 'getTransport', 'getExposure', 'getZoom', 'getPan',
              'getVoice', 'updateSettings']:
            return getattr(self.client, val, lambda: False)
        raise AttributeError


class CameraFactory(ClientFactory):
    FACTORY = None
    clients = {}
    listeners = {}
    pending = []

    @report(category=CATEGORY)
    def startedConnecting(self, connector):
        pass

    @report(category=CATEGORY)
    def buildProtocol(self, addr):
        log.msg("Connected %s" % str(addr))
        if addr in CameraFactory.pending:
            CameraFactory.pending.remove(addr)
        from airi.api import UpdateManager
        UpdateManager.propagate(addr[0], {"status": True})
        CameraFactory.clients[addr[0]] = Camera(addr[0])
        CameraFactory.clients[addr[0]].gotFrame = partial(
            CameraFactory.gotFrame, addr[0])
        return CameraFactory.clients[addr[0]]

    #@report(category=CATEGORY)
    @classmethod
    def gotFrame(klass, addr, frame):
        if addr not in klass.listeners:
            return
        for listener in klass.listeners[addr]:
            listener.gotFrame(frame, address=addr)

    @classmethod
    @report(category=CATEGORY)
    def setSize(klass, addr, size):
        klass.clients[addr].client.setSize(size)

    @classmethod
    @report(category=CATEGORY)
    def getSize(klass, addr):
        return klass.clients[addr].client.getSize()

    @classmethod
    @report(category=CATEGORY)
    def getSizes(klass, addr):
        return klass.clients[addr].client.getSizes()

    @classmethod
    @report(category=CATEGORY)
    def __cleanup(klass, addr):
        if addr in klass.listeners:
            del klass.listeners[addr]
        if addr in klass.clients:
            if getattr(klass.clients[addr], "client", None):
                del klass.clients[addr].client
            del klass.clients[addr]

    @report(category=CATEGORY)
    def __lostConnection(self, addr, reason, failed):
        rep = False

        if addr in CameraFactory.pending:
            CameraFactory.pending.remove(addr)

        if addr in CameraFactory.listeners:
            for listener in CameraFactory.listeners[addr]:
                rep = rep or listener.lostConnection(reason, failed,
                                    address=addr)

        if not rep:
            CameraFactory.__cleanup(addr)
        from airi.api import UpdateManager
        UpdateManager.propagate(addr, {"status": False})

        if __name__ == '__main__' and reactor.running:
            reactor.stop()

    @report(category=CATEGORY)
    def clientConnectionLost(self, connector, reason):
        addr = connector.getDestination()[0]
        log.msg("Lost connection to %s. Reason: %s" % (addr, reason))
        self.__lostConnection(addr, reason, False)

    @report(category=CATEGORY)
    def clientConnectionFailed(self, connector, reason):
        addr = connector.getDestination()[0]
        log.msg("Connection Failed to %s. Reason: %s" % (addr, reason))
        self.__lostConnection(addr, reason, True)

    @classmethod
    @report(category=CATEGORY)
    def isConnected(klass, addr):
        return addr in klass.clients

    @classmethod
    @report(category=CATEGORY)
    def isPending(klass, addr):
        return addr in klass.pending

    @classmethod
    @report(category=CATEGORY)
    def connect(klass, address, channel=1, method="RFCOMM"):
        if klass.isConnected(address):
            raise Exception("All ready connected to %s" % address)

        if klass.isPending(address):
            raise Exception("Connection to %s is pending" % address)

        klass.pending.append(address)
        settings = klass.getCamera(address, True)
        method = getattr(settings, "transport", method)
        c = getattr(twisted_bluetooth, "connect%s" % method)

        if klass.FACTORY == None:
            klass.FACTORY = klass()

        if method == "RFCOMM":
            channel = 1
        elif method == "L2CAP":
            channel = 0x1001
        log.msg("Connecting to %s using %s channel %s" %
                (address, method, channel))

        from airi.api import UpdateManager
        UpdateManager.propagate(address, {"status": "Connecting"})
        c(reactor, address, channel, klass.FACTORY)

    @classmethod
    @report(category=CATEGORY)
    def disconnect(klass, address):
        if klass.isConnected(address):
            try:
                klass.clients[address].client.disconnect()
                klass.clients[address].transport.loseConnection()
            except Exception, err:
                log.msg("call to disconnect failed")
                log.err(err)
        if address in klass.listeners:
            for listener in klass.listeners[address]:
                if getattr(listener, 'forcedDisconnect', None):
                    try:
                        listener.forcedDisconnect(address=address)
                    except:
                        pass
        klass.__cleanup(address)

    @classmethod
    @report(category=CATEGORY)
    def registerListener(klass, address, listener):
        if not address in klass.listeners:
            klass.listeners[address] = list()

        if listener not in klass.listeners[address]:
            dbg("adding listener")
            klass.listeners[address].append(listener)

    @classmethod
    @report(category=CATEGORY)
    def removeListener(klass, address, listener):
        try:
            klass.listeners[address].remove(listener)
        except:
            pass

    @classmethod
    @report(category=CATEGORY)
    def getConnected(klass, address=None):
        if address:
            return klass.clients.get(str(address.strip()), None)
        return klass.clients

    @classmethod
    @report(category=CATEGORY)
    def getCamera(klass, address, silent=False):
        out = settings.getCamera(address)
        if not out:
            if not silent:
                raise UnknownDevice(address)
            return None

        out["status"] = klass.isConnected(address)
        if klass.isConnected(address):
            out["name"] = twisted_bluetooth.resolve_name(address)
            settings.setCamera(out)
            settings.save()
        out["capabilities"] = TYPES[out["type"]]["class"].Capabilities
        return out

    @classmethod
    @report(category=CATEGORY)
    def getCameras(klass):
        for camera in settings.getCameras():
            yield klass.getCamera(camera["address"])

    @classmethod
    def getTypes(klass):
        return TYPES.keys()


if __name__ == '__main__':
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
