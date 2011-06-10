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
import socket
import sys
import operator
import bluetooth
import struct

from twisted.internet import tcp, reactor
from twisted.internet.tcp import *

from errno import EBADFD

from twisted.python import log

from bluetooth import *
import bluetooth._bluetooth as bt

SPP_UUID="00001101-0000-1000-8000-00805F9B34FB"
if __name__=='__main__':
	from dbus.mainloop.glib import DBusGMainLoop
	DBusGMainLoop(set_as_default=True)

flag = False
def initalizeDBus():
	global flag
	if flag:
		return

	global dbus, bus, manager
	try:
		import dbus
		try:
			bus = dbus.SessionBus()
			manager = dbus.Interface(bus.get_object("org.bluez", "/"),
				"org.bluez.Manager")
		except:
			bus = dbus.SystemBus()
			manager = dbus.Interface(bus.get_object("org.bluez", "/"),
				"org.bluez.Manager")
		log.msg("DBus available")
		flag = True
	except Exception, err:
		log.msg("DBus unavailable")
		log.error(err)
		if isAndroid(): flag = True

def isAndroid():
	try:
		global droid
		import android
		droid=android.API()
		return True
	except:
		pass
	return False

def androidIsBonded(address):
	try:
		global droid
		r = droid.bluetoothIsBonded(address)
		return r
	except Exception, err:
		log.err(err)
	return False

def bluezIsBonded(address):
	initalizeDBus()
	global dbus, bus, manager
	
	adapter = dbus.Interface(bus.get_object("org.bluez",
		manager.DefaultAdapter()), "org.bluez.Adapter")
	try:
		dev = adapter.FindDevice(address)
	except Exception, err:
		return False
	dev = dbus.Interface(bus.get_object("org.bluez",dev),
			"org.bluez.Device")
	return bool(dev.GetProperties()["Paired"])
	
def isBonded(address):
	if isAndroid():
		return androidIsBonded(address)
	return bluezIsBonded(address)

def androidBondDevice(address):
	res = droid.bluetoothConnect(SPP_UUID, address) 
	droid.bluetoothStop(res)

def bluezBondDevice(address):
	initalizeDBus()
	global dbus, bus, manager
	
	from airi.pair import Agent, PATH
	path = "%s/temp/%s" % (PATH, address.replace(":", ""))
	agent = Agent(bus, path)
	agent.set_exit_on_release(False)
	adapter = dbus.Interface(bus.get_object("org.bluez",
		manager.DefaultAdapter()), "org.bluez.Adapter")
	log.msg("Bonding device")
	adapter.CreatePairedDevice(address, path,
			"KeyboardOnly", reply_handler=lambda X: None,
			error_handler=lambda X: None)

def bondDevice(address):
	if isAndroid():
		return androidBondDevice(address)
	return bluezBondDevice(address)

def isPairingSupported():
	if isAndroid():
		return False
	print "isPairingSupported", True
	return True

def isPairingReady():
	if not isPairingSupported():
		return False
	return len(Agent.listeners)>0

class BluetoothConnection(tcp.Connection):
	"""
	Superclass of all Bluetooth-socket-based Descriptors

	This is an abstract superclass of all objects which represent a Bluetooth
	connection based socket.

	@ivar logstr: prefix used when logging events related to this connection.
	@type logstr: C{str}

	"""

class BluetoothBaseClient(tcp.Connection):
	"""A base class for client Bluetooth (and similiar) sockets.
	"""
	addressFamily = 31 # AF_BLUETOOTH
	proto = None

	def createInternetSocket(self):
		"""(internal) Create a non-blocking socket using
		self.addressFamily, self.socketType.
		"""
		if self.proto not in [ None, bluetooth.RFCOMM, bluetooth.SCO, 
				bluetooth.HCI, bluetooth.L2CAP ]:
			raise RuntimeException("I only handle bluetooth sockets")

		print self.proto, type(self.proto)
		s = bluetooth.BluetoothSocket(self.proto)
		s.setblocking(0)
		tcp.fdesc._setCloseOnExec(s.fileno())
		return s
	
	def resolveAddress(self):
		self.realAddress = self.addr
		print "resolveAddress", self.realAddress
		self.doConnect()

	def doConnect(self):
		"""I connect the socket.

		Then, call the protocol's makeConnection, and start waiting for data.
		"""
		if not hasattr(self, "connector"):
			# this happens when connection failed but doConnect
			# was scheduled via a callLater in self._finishInit
			return

		err = self.socket.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
		if err:
			self.failIfNotConnected(error.getConnectError((err, strerror(err))))
			return

		# doConnect gets called twice.  The first time we actually need to
		# start the connection attempt.  The second time we don't really
		# want to (SO_ERROR above will have taken care of any errors, and if
		# it reported none, the mere fact that doConnect was called again is
		# sufficient to indicate that the connection has succeeded), but it
		# is not /particularly/ detrimental to do so.  This should get
		# cleaned up some day, though.
		try:
			connectResult = self.socket.connect_ex(self.realAddress)
		except socket.error, se:
			connectResult = se.args[0]
		print "connectResult", connectResult
		if connectResult:
			if connectResult == EISCONN or connectResult == EBADFD:
				pass 
			elif connectResult in (EWOULDBLOCK, EINPROGRESS, EALREADY):
				self.startReading()
				self.startWriting()
				return
			else:
				self.failIfNotConnected(error.getConnectError((connectResult, 
					strerror(connectResult))))
				return

		# If I have reached this point without raising or returning, that means
		# that the socket is connected.
		del self.doWrite
		del self.doRead
		# we first stop and then start, to reset references to the old doRead
		self.stopReading()
		self.stopWriting()
		self._connectDone()

	def doRead(self):
		"""Calls self.protocol.dataReceived with all available data.

		This reads up to self.bufferSize bytes of data from its socket, then
		calls self.dataReceived(data) to process it.  If the connection is not
		lost through an error in the physical recv(), this function will return
		the result of the dataReceived call.
		"""
		try:
			data = self.socket.recv(self.bufferSize)
		except (bluetooth.btcommon.BluetoothError, socket.error), se:
			if se.args[0] == EWOULDBLOCK:
				return
			else:
				return main.CONNECTION_LOST
		if not data:
			return main.CONNECTION_DONE
		return self.protocol.dataReceived(data)



class Client(BluetoothBaseClient, tcp.Client):
	"""A Bluetooth client."""

	def __init__(self, proto, *args, **kwargs):
		if proto not in [ None, bluetooth.RFCOMM, bluetooth.SCO, bluetooth.HCI, 
				bluetooth.L2CAP ]:
			raise RuntimeException("I only handle bluetooth sockets")
		self.proto = proto
		super(Client, self).__init__(*args, **kwargs)

	def getHost(self):
		"""Returns a Bluetooth address.

		This indicates the address from which I am connecting.
		"""
		return self.socket.getsockname()

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

	def startTLS(self, ctx, server=1):
		raise RuntimeException("not valid method")

	def getHost(self):
		"""Returns a Bluetooth address.

		This indicates the server's address.
		"""
		return self.socket.getsockname()

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

	def __init__(self, proto, port, factory, backlog=50, interface='', 
			reactor=None):
		"""Initialize with a numeric port to listen on.
		"""
		tcp.Port.__init__(self, port, factory, backlog, interface, reactor)
		if proto not in [ None, bluetooth.RFCOMM, bluetooth.SCO, bluetooth.HCI, 
				bluetooth.L2CAP ]:
			raise RuntimeException("I only do Bluetooth")
		self.proto = proto

	def createInternetSocket(self):
		s = bluetooth.BluetoothSocket(self.proto)
		if platformType == "posix" and sys.platform != "cygwin":
			s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		return s

	def _buildAddr(self, (host, port)):
		return (host, port)

	def getHost(self):
		"""Returns a Bluetooth Address

		This indicates the server's address.
		"""
		return self.socket.getsockname()

class Connector(tcp.Connector):
	def __init__(self, proto, host, port, *a, **kw):
		tcp.Connector.__init__(self, host, int(port), *a, **kw)
		self.proto = proto

	def _makeTransport(self):
		return Client(self.proto, self.host, self.port, self.bindAddress, self, 
				self.reactor)

	def getDestination(self):
		return (self.host, self.port)

def __connectGeneric(reactor, proto, host, port, factory, timeout=30, 
		bindAddress=None):
	if not isBonded(host) and proto != bluetooth.SCO:
		bondDevice(host)
	c = Connector(proto, host, port, factory, timeout, bindAddress, reactor)
	c.connect()
	return c

def connectRFCOMM(reactor, *a, **kw):
	return __connectGeneric(reactor, bluetooth.RFCOMM, *a, **kw)

def connectL2CAP(reactor, *a, **kw):
	return __connectGeneric(reactor, bluetooth.L2CAP, *a, **kw)

def setupSCO():
	# check voice settings. switch to S16 LE mono 8kHz CVSD if needed
	hci_sock=bt.hci_open_dev()
	response = bt.hci_send_req(hci_sock, bt.OGF_HOST_CTL, 
			bt.OCF_READ_VOICE_SETTING, bt.EVT_CMD_COMPLETE, 3)
	status, voice_setting = struct.unpack("<BH", response)
	if voice_setting != 0x60:
		new_vs = struct.pack("<H", 0x60)
		bt.hci_send_req(hci_sock, bt.OGF_HOST_CTL, 
			bt.OCF_WRITE_VOICE_SETTING, 
			bt.EVT_CMD_COMPLETE, 1, new_vs)

	# determine the maximun packet size
	response = bt.hci_send_req(hci_sock, bt.OGF_INFO_PARAM, 
	bt.OCF_READ_BUFFER_SIZE, bt.EVT_CMD_COMPLETE, 8)
	status, acl_mtu, sco_mtu, acl_nbufs, sco_nbufs = struct.unpack(
				">BHBHH", response)
	return acl_mtu, sco_mtu, acl_nbufs, sco_nbufs
acl_mtu, sco_mtu, acl_nbufs, sco_nbufs = setupSCO()

def connectSCO(reactor, *a, **kw):
	return __connectGeneric(reactor, bluetooth.SCO, *a, **kw)

def resolve_name(address):
	sock = bluetooth.bluez._gethcisock()
	out = None
	try:
		out = bluetooth.bluez._bt.hci_read_remote_name(sock, address)
	except:
		pass
	sock.close()
	return out

def SCOConnected(target):
	return target.lower() in SCOReader.clients

def SCODisconnect(target):
	if not SCOConnected(target):
		return
	c = SCOReader.clients[target.lower()]
	c.close()

class SCOReader(object):
	sock = None
	listener = None
	clients = {}

	def __init__(self, target, listener = None, connectionLost = None):
		if SCOConnected(target):
			log.error("Can't connect twice to the same device")
			return

		self.sock = bluetooth.BluetoothSocket(bluetooth.SCO)
		try:
			self.sock.connect((target,))
		except Exception, err:
			log.error("Failed while trying to connect SCO")
			log.error(err)
			return
		self.sock.setblocking(False)
		self.address = target.lower()
		self._listener = listener
		self._connectionLost = connectionLost
		SCOReader.clients[target.lower()]=self
		reactor.addReader(self)

	def isConnected(self):
		return self.sock != None

	def fileno(self):
		return self.sock.fileno()

	def doRead(self):
		self._listener(self)

	def close(self):
		reactor.removeReader(self)
		self.sock.setblocking(True)
		self.sock.close()
		self.sock = None
		if self.address.lower() in SCOReader.clients:
			del SCOReader.clients[self.address.lower()]

	def logPrefix(self): 
		return "SCO-Reader"

	def connectionLost(self, reason):
		if callable(self._connectionLost):
			try:
				self._connectionLost(self)
			except Exception, err:
				log.error(err)
		if self.address.lower() in SCOReader.clients:
			del SCOReader.clients[self.address.lower()]
	
	def recv(self, *args, **kwargs):
		return self.sock.recv(*args, **kwargs)

if __name__=='__main__':
	import sys
	address = sys.argv[1]
	import airi.pair as pair
	def main():
		initalizeDBus()
		global dbus, bus, manager
		agent = pair.Agent(bus, pair.PATH)
		print isBonded(address)
		print bondDevice(address)
		print isBonded(address)
		reactor.stop()
	from twisted.internet import reactor
	reactor.callWhenRunning(main)
	reactor.run()

