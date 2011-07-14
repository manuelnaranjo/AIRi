import sys, os, socket, json, errno, time
from android import API
from twisted.internet import reactor
from twisted.python import log
droid = API()
os.environ["HOME"] = "/data/data/net.aircable.airi/files"

class EventSocket(object):
    # based on https://github.com/jdavisp3/twisted-intro/raw/master/twisted-client-1/get-poetry.py
    socket = None
    bytes = ""

    def __init__(self, address):
        self.address = address
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(address)
        self.socket.setblocking(0)
        self.bytes = ""

        # tell the Twisted reactor to monitor this socket for reading
        from twisted.internet import reactor
        reactor.addReader(self)

    def fileno(self):
        try:
            return self.socket.fileno()
        except socket.error:
            return -1

    def connectionLost(self, reason):
        self.socket.close()
        # it may happen that the sl4a dies
        try:
            reactor.stop()
        except:
            pass

    def handleEvent(self, name, data, time):
        if name=='airi':
            if data=='exit':
                droid.log("Got Exit!")
                reactor.stop()

    def doRead(self):
        while True:
            try:
                bytesread = self.socket.recv(1024)
                if not bytesread:
                    break
                else:
                    self.bytes += bytesread
            except socket.error, e:
                if e.args[0] == errno.EWOULDBLOCK:
                    break
                return main.CONNECTION_LOST

        droid.log("Got: %s" % self.bytes)
        for line in self.bytes.splitlines(True):
            if '\n' in line:
                ev = {"data": None, "name": None, "time": None}
                ev.update(json.loads(line[:-1]))
                droid.log("%s %s" % (type(ev), ev))
                self.handleEvent(**ev)

        self.bytes = self.bytes[self.bytes.rfind("\n")+1:]

    def logPrefix(self):
        return "EventSocket"

def start_browser(listener):
    droid.log(str(listener))
    droid.log("starting view in port %s" % listener._realPortNumber)
    droid.webViewShow("http://127.0.0.1:%s/index.html" % listener._realPortNumber)
    droid.addOptionsMenuItem("Exit", "airi", "exit", "ic_menu_close_clear_cancel")
    droid.airiHideSplashScreen();
    droid.dialogCreateSpinnerProgress("AIRi", "AIRi is Loading. Please wait...");
    droid.dialogShow();

def main():
    droid.log("Checking if bluetooth is available")
    if not droid.checkBluetoothState():
        droid.toggleBluetoothState(True, True)
        if not droid.checkBluetoothState():
            droid.makeToast("I can't work if you don't enable Bluetooth")
            time.sleep(1)
            sys.exit(1)
    from airi.jinja import main as jmain
    from airi.stream import MultiPartStream
    droid.log("Starting server")
    l = jmain(port=0)
    portnumber = int(droid.startEventDispatcher())
    sockl = EventSocket(('127.0.0.1', portnumber))
    reactor.callWhenRunning(start_browser, listener=l)
    reactor.run()
    droid.log("Reactor stopped")
    droid.airiRemoveNotification()

