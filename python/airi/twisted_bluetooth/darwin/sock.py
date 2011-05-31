# -*- coding: utf-8 -*-
# Copyright (c) 2011 Naranjo Manuel Francisco <manuel@aircable.net>
# Copyright (c) 2001-2009 Twisted Matrix Laboratories.
# See Twisted LICENSE for details.

"""
Various Bluetooth Socket classes
"""

# System Imports
import os
import types
import sys
import operator
import lightblue as bluetooth
from lightblue import *
import socket

from twisted.internet import tcp
from twisted.internet.tcp import *

from twisted.python import log

from airi import report

CATEGORY="darwin"

from multiprocessing.connection import Listener
def isPairingSupported():
	return False

@report(category=CATEGORY)
def discover_devices (duration=8, flush_cache=True, lookup_names=False):
    out = bluetooth.finddevices(getnames=lookup_names, length=duration)
    print out
    return [ (o[0], o[1]) for o in out ]

class BluetoothConnection(tcp.Connection):
    """
    Superclass of all Bluetooth-socket-based Descriptors

    This is an abstract superclass of all objects which represent a Bluetooth
    connection based socket.

    @ivar logstr: prefix used when logging events related to this connection.
    @type logstr: C{str}

    """

class ConnectionWrapper():
    def __init__(self, connection):
        self.__conn = connection
        for attr in dir(connection):
            if not attr.startswith("__"):
                if not getattr(self, attr, None):
                    setattr(self, attr, getattr(connection, attr))

    def send(self, what):
        if type(what) == buffer:
            what = str(buffer)
        self.__conn.send(what)
        return len(what)

    @report(category=CATEGORY)
    def bind(self, *args, **kwargs):
        pass

    @report(category=CATEGORY)
    def shutdown(self, *args, **kwargs):
        self.__conn.close()

    @report(category=CATEGORY)
    def setblocking(self, *args, **kwargs):
        pass

class BluetoothBaseClient(tcp.Connection):
    """A base class for client Bluetooth (and similiar) sockets.
    """
    addressFamily = 31 # AF_BLUETOOTH
    proto = None

    @report(category=CATEGORY)
    def createInternetSocket(self):
        """(internal) Create a non-blocking socket using
        self.addressFamily, self.socketType.
        """
        if self.proto not in [ None, bluetooth.RFCOMM, bluetooth.L2CAP ]:
            raise RuntimeException("I only handle bluetooth sockets")

        self.listener = Listener()
        pid = os.fork()
        if pid == 0:
            # I'm the child
            print "Child running"
            os.execvp(sys.executable, [sys.executable, "-m", "airi.twisted_bluetooth.darwin.helper",
                self.listener.address])
            # and we lost it
            print "OOOOOOOOOOOOOOOOOPPPPPPSSSSSSSS!!!!!!!!!"

        print "Luke I'm your father"
        self.childpid = pid
        s = self.listener.accept()
        return ConnectionWrapper(s)

    @report(category=CATEGORY)
    def resolveAddress(self):
        self.realAddress = self.addr
        print "resolveAddress", self.realAddress
        self.doConnect()

    @report(category=CATEGORY)
    def doConnect(self):
        """I connect the socket.

        Then, call the protocol's makeConnection, and start waiting for data.
        """
        if not hasattr(self, "connector"):
            # this happens when connection failed but doConnect
            # was scheduled via a callLater in self._finishInit
            return

        self.socket.send([self.proto, self.realAddress])
        err = self.socket.recv()
        if err:
            self.socket.close()
            self.listener.close()
            os.waitpid(self.childpid, 0)
            self.failIfNotConnected(err)
            return

        # If I have reached this point without raising or returning, that means
        # that the socket is connected.
        del self.doWrite
        del self.doRead
        # we first stop and then start, to reset any references to the old doRead
        self.stopReading()
        self.stopWriting()
        self._connectDone()

    @report(category=CATEGORY)
    def fileno(self):
        return self.socket.fileno()

    def doRead(self):
        """Calls self.protocol.dataReceived with all available data.

        This reads up to self.bufferSize bytes of data from its socket, then
        calls self.dataReceived(data) to process it.  If the connection is not
        lost through an error in the physical recv(), this function will return
        the result of the dataReceived call.
        """
        data = self.socket.recv()
        if type(data) != str:
            return main.CONNECTION_LOST
        return self.protocol.dataReceived(data)

class Client(BluetoothBaseClient, tcp.Client):
    """A Bluetooth client."""

    @report(category=CATEGORY)
    def __init__(self, proto, *args, **kwargs):
        if proto not in [ None, bluetooth.RFCOMM, bluetooth.L2CAP ]:
            raise RuntimeException("I only handle bluetooth sockets")
        self.proto = proto
        super(Client, self).__init__(*args, **kwargs)

    @report(category=CATEGORY)
    def getHost(self):
        """Returns a Bluetooth address.

        This indicates the address from which I am connecting.
        """
        return self.socket.getsockname()

    @report(category=CATEGORY)
    def getPeer(self):
        """Returns a Bluetooth address.

        This indicates the address that I am connected to.
        """
        return self.realAddress

class Server(BluetoothBaseClient, tcp.Connection):
    """
    Serverside bluetooth socket-stream connection class.

    This is a serverside network connection transport; a socket which came from
    an accept() on a server.
    """

    @report(category=CATEGORY)
    def startTLS(self, ctx, server=1):
        raise RuntimeException("not valid method")

    @report(category=CATEGORY)
    def getHost(self):
        """Returns a Bluetooth address.

        This indicates the server's address.
        """
        return self.socket.getsockname()

    @report(category=CATEGORY)
    def getPeer(self):
        """Returns a Bluetooth address.

        This indicates the client's address.
        """
        return self.client

class Port(tcp.Port):
    """
    A Bluetooth server port, listening for connections.

    L{twisted.internet.tcp.Port}
    """
    addressFamily = 31 # socket.AF_BLUETOOTH
    proto = None

    @report(category=CATEGORY)
    def __init__(self, proto, port, factory, backlog=50, interface='', reactor=None):
        """Initialize with a numeric port to listen on.
        """
        tcp.Port.__init__(self, port, factory, backlog, interface, reactor)
        if proto not in [ None, bluetooth.RFCOMM, bluetooth.L2CAP ]:
            raise RuntimeException("I only do Bluetooth")
        self.proto = proto

    @report(category=CATEGORY)
    def createInternetSocket(self):
        s = bluetooth.BluetoothSocket(self.proto)
        if platformType == "posix" and sys.platform != "cygwin":
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s

    @report(category=CATEGORY)
    def _buildAddr(self, (host, port)):
        return (host, port)

    @report(category=CATEGORY)
    def getHost(self):
        """Returns a Bluetooth Address

        This indicates the server's address.
        """
        return self.socket.getsockname()

class Connector(tcp.Connector):
    @report(category=CATEGORY)
    def __init__(self, proto, host, port, *a, **kw):
        tcp.Connector.__init__(self, host, int(port), *a, **kw)
        self.proto = proto

    @report(category=CATEGORY)
    def _makeTransport(self):
        return Client(self.proto, self.host, self.port, self.bindAddress, self, self.reactor)

    @report(category=CATEGORY)
    def getDestination(self):
        return (self.host, self.port)

@report(category=CATEGORY)
def __connectGeneric(reactor, proto, host, port, factory, timeout=30, bindAddress=None):
    c = Connector(proto, host, port, factory, timeout, bindAddress, reactor)
    c.connect()
    return c

@report(category=CATEGORY)
def connectRFCOMM(reactor, *a, **kw):
    return __connectGeneric(reactor, bluetooth.RFCOMM, *a, **kw)

@report(category=CATEGORY)
def connectL2CAP(reactor, *a, **kw):
    return __connectGeneric(reactor, bluetooth.L2CAP, *a, **kw)

@report(category=CATEGORY)
def resolve_name(address):
    try:
        return bluetooth.finddevicename(address, True)
    except Exception, err:
        print err
    return None


