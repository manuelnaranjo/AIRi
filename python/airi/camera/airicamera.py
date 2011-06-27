# -*- coding: utf-8 -*-
from twisted.python import log
from twisted.internet import reactor
from airi.camera import dbg, CameraProtocol
from airi.settings import getSettings
from datetime import datetime
import airi.twisted_bluetooth as bluetooth

settings = getSettings()

SIZES = {
    #day modes
    "QVGA": 1,
    "VGA": 2,
    "XGA": 3,
    "QXGA": 5,
    "720P": 6,

    "QVGA Zoom 1": 11,
    "QVGA Zoom 2": 12,
    "QVGA Zoom 3": 13,
}

PANS = ["none", "right", "left", "up", "down"]

CAPABILITIES = {
    'size': [a[0] for a in sorted(SIZES.iteritems(), 
            key=lambda(x, y):(y, x))],
    'flash': True,
    'pan': PANS,
    'voice': False, # by now ;)
    'exposure': True,
    'transport': ['RFCOMM', 'L2CAP'],
    'battery': True,
}

COMMANDS = dict()


class Command():
    def __init__(self, name, timeout, command):
        self.name = name
        self.timeout = timeout
        self.command = command
        COMMANDS[name] = self

Command("date", 1, "D")
Command("flash", 1, "F")
Command("size", 3, "S")
Command("pan", 1, "P")
Command("exposure", 1, "E")
Command("stream", 1, "L")


class AIRi(CameraProtocol):
    client = None
    callLater = None
    size = "QVGA"
    defaults = {
        "size": "QVGA",
        "flash": 0,
        "voice": False,
        "exposure": 0,
        "stream": True,
        "pan": "none",
    }

    def getType(self):
        return 'AIRi'

    def __init__(self, client):
        self.client = client
        self.address = client.address
        self.transport = client.transport
        self.pending = []
        self.callLater = None
        self.sco_socket = None
        self.doSetup()
        self.buffer = ""

    def internalDoCommand(self):
        if len(self.pending) == 0:
            return
        command, value, timeout = self.pending.pop(0)
        if callable(value):
            value = value()
        dbg("doCommand $%s%s" % (command, value))
        self.transport.write("$%s%s\n\r" % (command, value))
        self.callLater = reactor.callLater(timeout, 
            self.internalDoCommand)

    def doCommand(self, command, value):
        if type(command) != Command:
            command = COMMANDS[command]
        self.pending.append((command.command, value, command.timeout))
        if self.callLater and self.callLater.active():
            return
        self.internalDoCommand()

    def doSetup(self):
        dbg("doSetup")
        nsets = settings.getCamera(self.address)
        sets = self.defaults
        size = self.size
        if nsets:
            sets.update(nsets)
        dbg(sets)
        self.callLater = reactor.callLater(1, self.internalDoCommand)
        self.doCommand("date",
                        lambda: datetime.utcnow().strftime("%Y%m%dT%H%M%SZ"))
        self.doCommand("size", SIZES[sets["size"]])
        self.doCommand("stream", "1" if sets["stream"] else "0")
        self.doCommand("flash", "0" if not sets["flash"] else "1")
        self.doCommand("pan", sets["pan"].upper()[0])

    def updateSettings(self):
        self.doSetup()

    def previewData(self):
        start = self.client.buffer.find("\xff\xd8")
        end = self.client.buffer.find("\xff\xd9")
        if start == -1 or end == -1:
            return

        frame = self.client.buffer[start:end + 2]
        self.client.buffer = self.client.buffer[end + 2:]
        self.client.gotFrame(frame)

    def SCO_Data(self, sock, lost=False):
        if lost:
            reactor.removeReader(self.sco_socket)
            return
        self.buffer += sock.recv(bluetooth.sco_mtu)
        if len(self.buffer) >= 400:
            from airi.stream import MultiPartStream
            MultiPartStream.sendToClients(self.buffer,
                mime="application/octet-stream")
            self.buffer = ""

    def enableSCO(self):
        if self.sco_socket != None:
            return

        self.sco_socket = bluetooth.SCOReader(self.address, self.SCO_Data)
        reactor.addReader(self.sco_socket)

    def disableSCO(self):
        if not self.sco_socket:
            return
        self.sco_socket.close()
        reactor.removeReader(self.sco_socket)
        self.sco_socket = None

    def doSCO(self, enable):
        if not getattr(bluetooth, "SCOReader", None):
            dbg("sco not supported in this platform")
            return
        if enable:
            return self.enableSCO()
        else:
            return self.disableSCO()

    def dataReceived(self):
        return self.previewData()

    def disconnect(self):
        dbg("AIRi.disconnect")
        self.disableSCO()

    def set(self, option, value):
        dbg("set %s-> %s" % (option, value))
        if option == "size":
            self.doCommand(option, SIZES[value])
        elif option == "flash" or option=="stream":
            self.doCommand(option, "0" if not value else "1")
        elif option == "pan" or option == "exposure":
            self.doCommand(option, value.upper())
        elif option == "voice":
            self.doSCO(value)
        else:
            dbg("ignored")

AIRi.Capabilities = CAPABILITIES
AIRi.Sizes = SIZES
AIRi.Panning = PANS

