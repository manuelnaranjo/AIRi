from twisted.web.resource import Resource
from twisted.web import http, server
from twisted.python import log
from twisted.internet import threads
from time import time
import json
import bluetooth
import traceback
from camera.protocol import CameraFactory
from settings import getSettings

settings = getSettings()

SCAN_TIMEOUT=60 # scan is started once each 60 seconds

def makeDictForClient(client, address):
  if client is None:
    return { 'error': 'Not Connected' }

  return { 
    'type':         client.getType(),
    'capabilities': client.getCapabilities(),
    'size':         client.getSize(),
    'flash':        client.getFlash(),
    'name':         client.getName(),
    'battery':      client.getBattery(),
    'transport':    client.getTransport(),
    'exposure':     client.getExposure(),
    'zoom':         client.getZoom(),
    'voice':        client.getVoice(),
    'pan':          client.getPan(),
    'reconnect':    client.getReconnect(),
    'reconnect_timeout': client.getReconnectTimeout(),
    'status':       CameraFactory.isConnected(address),
    'address':      address,
  }

class ConnectionTest():
  def __init__(self, req):
    self.request = req

  def cleanup(self, address):
    CameraFactory.disconnect(address)
    CameraFactory.removeListener(address, self)
    cli = CameraFactory.getCamera(address)
    self.request.write(json.dumps(cli))
    self.request.finish()

  def lostConnection(self, reason, failed, address):
    print "ConnectionTest.lostConnection", address
    self.cleanup(address)

  def gotFrame(self, frame, address):
    print "ConnectionTest.gotFrame", address

    self.cleanup(address)

class ConfigurationManager(Resource):
  isLeaf = True

  def render_GET(self, request):
    try:
      request.setHeader('Content-Type', 'application/json')
      request.setHeader('Cache-Control', 'no-cache')
      request.setHeader('Connection', 'close')
      address=request.postpath[0].replace("_", ":")
      return json.dumps(CameraFactory.getCamera(address))

    except Exception, err:
      CameraFactory.connect(address, 1, "RFCOMM")
      CameraFactory.registerListener(address, ConnectionTest(request))
      return server.NOT_DONE_YET

  def render_POST(self, request):
    out = {}
    print str(request.args)
    for key, value in request.args.iteritems():
      if len(value) > 1:
        out[key] = True
      else:
        out[key]=value[0]
    settings.setCamera(out)
    print out
    settings.save()
    cli = CameraFactory.getConnected(out['address'])
    if cli:
      cli.updateSettings()
    return "saved"


class ConnectionManager(Resource):
  isLeaf = True

  def render_all(self, request):
    out = {}
    for addr, cli in CameraFactory.getConnected().iteritems():
      out[addr] = CameraFactory.getCamera(addr)
    return out

  def render_GET(self, request):
    try:
      request.setHeader('Content-Type', 'application/json')
      request.setHeader('Cache-Control', 'no-cache')
      request.setHeader('Connection', 'close')
      if len(request.postpath) > 0 and len(request.postpath[0])>0:
        address=request.postpath[0].replace("_", ":")
        cli = CameraFactory.getCamera(address, silent=True)
        if cli is not None or not request.args.get("test", None):
          return json.dumps(CameraFactory.getCamera(address))
        CameraFactory.connect(address, 1, "RFCOMM")
        CameraFactory.registerListener(address, ConnectionTest(request))
        return server.NOT_DONE_YET
      else:
        return json.dumps(self.render_all(request))
    except Exception, err:
      request.setHeader('Content-Type', 'text/html')
      request.setHeader('Cache-Control', 'no-cache')
      request.setHeader('Connection', 'close')
      request.setResponseCode(500, str(err))
      return "<html><h1>ERROR:</h1>\n<pre>%s</pre></html>" % (traceback.format_exc())

class ScanManager(Resource):
  isLeaf = True
  lastscan = None
  scancache = None
  scanning = None
  waiting = []

  def do_work(self):
    error = None
    try:
      log.msg("Doing scan")
      cache = bluetooth.discover_devices(lookup_names=True)
      log.msg(cache)
      self.scancache = [{
          'address':x[0], 
          'name':x[1], 
          'state': CameraFactory.isConnected(x[0])}
          for x in cache]
      log.msg(self.scancache)
      remove = []
      print self.waiting
      for request in self.waiting:
        request.setHeader('Content-Type', 'application/json')
        request.setHeader('Cache-Control', 'no-cache')
        request.setHeader('Connection', 'close')
        request.write(json.dumps(self.scancache))
        request.finish()
      if len(self.waiting)==0:
        return
    except Exception, err:
      log.err(err)
      error = err

    try:
      error = "<html><h1>ERROR:</h1>\n<pre>%s</pre></html>" % traceback.format_exc()
      for request in self.waiting:
        if request.finished:
          continue
        request.setHeader('Content-Type', 'text/html')
        request.setHeader('Cache-Control', 'no-cache')
        request.setHeader('Connection', 'close')
        request.setResponseCode(500, error)
        request.write("<html><h1>ERROR:</h1>\n")
        request.write("<pre>%s</pre></html>" % traceback.format_exc())
        request.finish()
    except Exception, err:
      log.err(err)
    self.waiting = []
    self.lastscan = None
    log.msg("Scan thread done")


  def lost_connection(self, err, request):
    log.msg("lost_connection(%s)" % str(request))
    self.waiting.remove(request)
  
  def render_GET(self, request):
    if self.lastscan and time()-self.lastscan < SCAN_TIMEOUT:
      if not self.scancache:
        self.waiting.append(request)
        request.notifyFinish().addErrback(self.lost_connection, request)
        log.msg("%s" % self.waiting)
        log.msg("Tried to start a parallel scan, we wait")
        return server.NOT_DONE_YET

      request.setHeader('Content-Type', 'application/json')
      request.setHeader('Cache-Control', 'no-cache')
      request.setHeader('Connection', 'close')
      request.write(json.dumps(self.scancache))
      log.msg("Scan return from cache")
      return ''

    self.lastscan = time()
    self.waiting.append(request)
    request.notifyFinish().addErrback(self.lost_connection, request)
    log.msg("%s" % self.waiting)
    log.msg("Starting scan thread")
    threads.deferToThread(self.do_work)
    return server.NOT_DONE_YET

class API_Root(Resource):
  isLeaf = True

  def render_GET(self, request):
    return "Invalid"
    

class API(Resource):
  isLeaf = False

  def __init__(self, *a, **kw):
    log.msg("API()")
    Resource.__init__(self, *a, **kw)
    self.putChild("", API_Root())
    self.putChild("devices", ScanManager())
    self.putChild("connected", ConnectionManager())
    self.putChild("configure", ConfigurationManager())

if __name__=='__main__':
  from twisted.application.service import Application
  from twisted.application.internet import TCPServer
  from twisted.web.server import Site
  from twisted.internet import reactor
  import sys
  log.startLogging(sys.stdout)

  root = Resource()
  root.putChild("api", API())
  reactor.listenTCP(8800, Site(root), interface="0.0.0.0")
  reactor.run()#!/usr/bin/env python
