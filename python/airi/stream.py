#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time

from twisted.web import http, server
from twisted.internet import protocol
from twisted.internet import reactor
from twisted.internet import defer
from twisted.internet import task
from twisted.web.resource import Resource
from twisted.python import log
from logging import DEBUG
from airi.camera.protocol import CameraFactory
from airi.camera import Listener
from airi import report, RESULT
from functools import partial

MULTIPARTRESPONSE= "--%s\r\nContent-Type: %s\r\nContent-Size: %s\r\n\r\n%s\r\n\r\n"

CATEGORY = "AIRi-Stream"

class MultiPartStream():
  BOUNDARY = 'myBOUNDARY'
  clients = []
  request = None
  oneshot = False

  @report(category=CATEGORY)
  def __init__(self, request):
    self.request = request
    self.request.connectionLost = self.connectionLost
    self.request.multipart=self
    self.oneshot = self.request.args.get('oneshot', ['false',])[0].lower() == 'true'
    MultiPartStream.clients.append(self)

  @classmethod
  def getBoundary(klass):
    return "--%s\r\n" % (klass.BOUNDARY)

  def writeBoundary(self):
    self.request.write(MultiPartStream.getBoundary())

  def writeStop(self):
    self.request.write("%s--\r\n" % MultiPartStream.getBoundary())

  @report(category=CATEGORY)
  def process(self):
    if not self.oneshot:
      self.request.setHeader('Connection', 'Keep-Alive')
      if "flash" in self.request.args:
        self.request.setHeader('Content-Type', 
          'multipart/x-mixed-replace')
      else:
        self.request.setHeader('Content-Type', 
          'multipart/x-mixed-replace; boundary=%s' % (self.BOUNDARY))
    self.request.setHeader('Cache-Control', 'no-cache, no-store, must-revalidate;')
    self.request.setHeader('Expires', '0');
    self.request.setHeader('Pragma-directive', 'no-cache')
    self.request.setHeader('Pragma', 'no-cache')
    self.request.setHeader('Cache-directive', 'no-cache')

  @report(category=CATEGORY)
  def connectionLost(self, reason):
    MultiPartStream.clients.remove(self)

  @report(category=CATEGORY)
  def finish(self):
    try:
      self.request.finish()
    except Exception, err:
      log.err(err)

  def sendPart(self, content, mime="text/html", MULTIPART=None):
    if self.oneshot:
      try:
        self.request.setHeader("Content-Type", mime)
        self.request.setHeader("Content-Size", len(content))
        self.request.write(content)
        self.request.write("\n\n")
        self.finish()
      except Exception, err:
        log.msg("error during sendPart")
        log.err(err)
    else:
      if MULTIPART is None:
        MULTIPART=MULTIPARTRESPONSE % (MultiPartStream.BOUNDARY, mime, len(content), content)
      try:
        self.request.write(MULTIPART)
      except Exception, err:
        log.msg("error during sendPart")
        log.err(err)

  @report(category=CATEGORY)
  @classmethod
  def sendToClients(klass, content, mime="text/html"):
    if len(klass.clients) == 0:
      return

    size = len(content)
    out=MULTIPARTRESPONSE % (klass.BOUNDARY, mime, size, content)

    for client in klass.clients:
      client.sendPart(content, mime, out)

    log.msg("sendToClients, size: %s, count: %s" %(len(content), len(klass.clients)), 
      loglevel=DEBUG,
      category="MultiPartStream")

class StreamResource(Resource, Listener):
  isLeaf = True

  def gotFrame(self, frame, address):
    #print "StreamResource.gotFrame %s" % len(frame)
    size = len(frame)
    out=MULTIPARTRESPONSE % (MultiPartStream.BOUNDARY, "image/jpeg", size, frame)

    for client in MultiPartStream.clients:
      if client.target == address:
        client.sendPart(frame, "image/jpeg")

  @report(category=CATEGORY)
  def lostConnection(self, reason, failed, address):
    print "StreamResource.lostConnection", address
    clients = [ a for a in MultiPartStream.clients if a.target == address ]
    for c in clients:
      c.sendPart(str(reason))
      if not c.oneshot:
        try:
          c.request.finish()
        except Exception, err:
          log.err(err)
      MultiPartStream.clients.remove(c)

  @report(category=CATEGORY, level=RESULT)
  def render_GET(self, request):
    address = request.path.split("/",2)[-1].replace("_", ":")
    request.transport.socket.settimeout(5)
    multipart = MultiPartStream(request)
    multipart.process()
    multipart.target = address
    if len(address) == 17:
      ready = CameraFactory.isConnected(address) or CameraFactory.isPending(address)
      if not ready:
        method = request.args.get("method", ["RFCOMM",])[-1]
        try:
          CameraFactory.connect(address, 1, method)
        except Exception, err:
          log.msg("Failed while trying to connect")
          log.err(err)
    CameraFactory.registerListener(address, self)
    return server.NOT_DONE_YET

class TestStreamResource(Resource):
  isLeaf = True

  def render_GET(self, request):
    log.msg(str(request))
    log.msg(str(request.requestHeaders))
    multipart = MultiPartStream(request)
    multipart.process()
    return server.NOT_DONE_YET

  def render_POST(self, request):
    return self.render_GET(request)

if __name__ == '__main__':
  import webcam
  from twisted.web.server import Site
  import sys
  log.startLogging(sys.stdout)

  webcam.init(False)
  def sendFrame():
    MultiPartStream.sendToClients(webcam.repeat().tostring(), "image/jpeg")
    reactor.callLater(1/15., sendFrame)

  root = Resource()
  root.isLeaf = False
  root.putChild("stream", TestStreamResource())
  reactor.listenTCP(8800, Site(root), interface="0.0.0.0")
  reactor.callLater(0, sendFrame)
  reactor.run()#!/usr/bin/env python
