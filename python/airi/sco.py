#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time, wave, struct, array

from twisted.web import http, server
from twisted.internet import protocol
from twisted.internet import reactor
from twisted.internet import defer
from twisted.internet import task
from twisted.web.resource import Resource
from twisted.python import log
from logging import DEBUG
from airi.camera import airicamera
from airi.camera.protocol import CameraFactory
from airi.camera import Listener
from airi import report, RESULT
from functools import partial
import twisted_bluetooth

HTTP_DISCONNECT_TIMEOUT = 10
CATEGORY = "AIRi-SCO"

class SCOStream():
	clients = []
	request = None

	@report(category=CATEGORY)
	def __init__(self, request):
		self.request = request
		self.request.connectionLost = self.connectionLost
		self.request.multipart=self
		SCOStream.clients.append(self)

	@report(category=CATEGORY)
	def process(self):
		self.request.setHeader('Cache-Control', 
				'no-cache, no-store, must-revalidate;')
		self.request.setHeader('Expires', '0');
		self.request.setHeader('Pragma-directive', 'no-cache')
		self.request.setHeader('Pragma', 'no-cache')
		self.request.setHeader('Cache-directive', 'no-cache')
		self.request.setHeader('Content-Type', 'audio/x-wav')

		# based on wave.py from the batteries
		self.request.write("RIFF")
		initlength = 0x7fffffdb
		nchannels = 1
		sampwidth = 2
		framerate = 8000
		nframes = initlength / (nchannels * sampwidth)
		datalength = nframes * nchannels * sampwidth
		self.request.write(struct.pack('<l4s4slhhllhh4s',
			36 + datalength, 'WAVE', 'fmt ', 16,
			wave.WAVE_FORMAT_PCM, nchannels, framerate,
			nchannels * framerate * sampwidth,
			nchannels * sampwidth,
			sampwidth*8, 'data'))
		self.request.write(struct.pack('<l', datalength))

	@report(category=CATEGORY)
	def connectionLost(self, reason):
		'''Called when the http stream is closed'''
		if self in SCOStream.clients:
			SCOStream.clients.remove(self)
		if len(SCOStream.getClients(self.target)):
			return
		log.msg("No one else is listening, killing link")
		twisted_bluetooth.SCODisconnect(self.target)
		del self
	
	@classmethod
	def sendToClients(klass, data, address):
		if len(klass.clients) == 0:
			return

		nframes = len(data) // (2 * 1) #sampwidth * channels
		data = array.array("h", data)
		data.byteswap()
		data = data.tostring()
		for client in klass.getClients(address):
			client.request.write(data)

	@classmethod
	def getClients(klass, address):
		def internal():
			for c in klass.clients:
				if c.target.lower() == address:
					yield c
		address = address.lower()
		return list(internal())

class SCOResource(Resource, Listener):
	isLeaf = True
  
	@classmethod
	def getClients(klass, address):
		return SCOStream.getClients(address)

	def gotFrame(self, client):
		data = client.recv(4096)
		SCOStream.sendToClients(data, client.address)

	@report(category=CATEGORY)
	def lostConnection(self, client):
		'''Called when the Bluetooth Link is lost'''
		print "SCOResource.lostConnection", client.address
		clients = SCOStream.getClients(client.address)
		for c in clients:
			try:
				c.request.finish()
			except Exception, err:
				log.err(err)
			SCOStream.clients.remove(c)

	@report(category=CATEGORY, level=RESULT)
	def render_GET(self, request):
		request.transport.socket.settimeout(5)
		if not getattr(twisted_bluetooth, "SCOReader", None):
			raise Exception("Not supported in your platform")

		address = request.path.split("/",2)[-1].replace("_", ":")
		if address == "" or len(address) != 17:
			raise Exception("Invalid address")
		scoclient = SCOStream(request)
		scoclient.process()
		scoclient.target = address
		if len(address) == 17:
			if not twisted_bluetooth.SCOConnected(address):
				log.msg("Connecting SCO to %s" % address)
				client = twisted_bluetooth.SCOReader(address,
						self.gotFrame, self.lostConnection)
				log.msg("SCO connected")
		return server.NOT_DONE_YET

if __name__ == '__main__':
	from twisted.web.server import Site
	import sys
	log.startLogging(sys.stdout)

	root = Resource()
	root.isLeaf = False
	root.putChild("sco", SCOResource())
	reactor.listenTCP(8800, Site(root), interface="0.0.0.0")
	reactor.run()#!/usr/bin/env python

