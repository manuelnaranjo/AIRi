from twisted.web.resource import Resource
from twisted.web import http, server
from twisted.python import log
from twisted.internet import threads, reactor
from time import time
import json
import twisted_bluetooth as bluetooth
import traceback
from airi.camera.protocol import CameraFactory
from airi.settings import getSettings
from airi import report

settings = getSettings()

SCAN_TIMEOUT=60 # scan is started once each 60 seconds

class ConnectionTest():
  def __init__(self, req):
    self.request = req

  def cleanup(self, address):
    CameraFactory.disconnect(address)
    CameraFactory.removeListener(address, self)
    self.request.finish()

  def lostConnection(self, reason, failed, address):
    print "ConnectionTest.lostConnection", address
    self.request.write("<html><h1>ERROR:</h1>\n<pre>%s</pre></html>" % reason)
    self.request.setResponseCode(500, str(failed))
    self.cleanup(address)

  def gotFrame(self, frame, address):
    print "ConnectionTest.gotFrame", address
    cli = CameraFactory.getCamera(address)
    self.request.write(json.dumps(cli))
    self.cleanup(address)

class DevicesManager(Resource):
  isLeaf = True
  
  def render_GET(self, request):
    request.setHeader('Content-Type', 'application/json')
    request.setHeader('Cache-Control', 'no-cache')
    request.setHeader('Connection', 'close')
    return json.dumps(list(CameraFactory.getCameras()))

class ConfigurationManager(Resource):
  isLeaf = True

  def render_GET(self, request):
    try:
      request.setHeader('Content-Type', 'application/json')
      request.setHeader('Cache-Control', 'no-cache')
      request.setHeader('Connection', 'close')
      if len(request.postpath) > 0 and len(request.postpath[0])>0:
        address=request.postpath[0].replace("_", ":")
        if len(request.args) == 0:
          return json.dumps(CameraFactory.getCamera(address))
        camera = settings.getCamera(address)
        for key in request.args:
            settings.setCameraSetting(address, key, request.args[key][-1])
        settings.save()
        cli = CameraFactory.getConnected(address)
        if cli:
          cli.updateSettings()
        return json.dumps(CameraFactory.getCamera(address))
      request.setResponseCode(500, "invalid address")
      return "Invalid address"

    except Exception, err:
      print err
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

class doConfiguration(Resource):
  isLeaf = True

  def render_POST(self, request):
    address = request.args["address"][0]
    option = request.args["option"][0]
    value = request.args["value"][0]
    print address, option, value
    try:
      cli = CameraFactory.getConnected(address)
      if cli:
        cli.client.set(option, value)
      return "updated"
    except Exception, err:
      return "failed: %s" % err

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
        if cli or not request.args.get("test", None):
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

class DisconnectManager(Resource):
  isLeaf = True

  def render_GET(self, request):
    try:
      request.setHeader('Content-Type', 'application/json')
      request.setHeader('Cache-Control', 'no-cache')
      request.setHeader('Connection', 'close')
      if len(request.postpath) > 0 and len(request.postpath[0])>0:
        address=request.postpath[0].replace("_", ":")
        if not CameraFactory.isConnected(address):
          return json.dumps({"result": "Not Connected"})
        CameraFactory.disconnect(address)
        return json.dumps({"result": "Disconnected"})
      return json.dumps({"result": "No Address"})
    except Exception, err:
      request.setHeader('Content-Type', 'text/html')
      request.setHeader('Cache-Control', 'no-cache')
      request.setHeader('Connection', 'close')
      request.setResponseCode(500, str(err))
      return "<html><h1>ERROR:</h1>\n<pre>%s</pre></html>" % (traceback.format_exc())

class StateManager(Resource):
  isLeaf = True

  def render_POST(self, request):
    try:
      request.setHeader('Content-Type', 'application/json')
      request.setHeader('Cache-Control', 'no-cache')
      request.setHeader('Connection', 'close')
      address = request.args["address"][0]
      if CameraFactory.isConnected(address):
        CameraFactory.disconnect(address)
        return json.dumps({"result": "disconnected"})
      else:
        CameraFactory.connect(address)
        return json.dumps({"result": "connecting"})
    except Exception, err:
      request.setHeader('Content-Type', 'text/html')
      request.setHeader('Cache-Control', 'no-cache')
      request.setHeader('Connection', 'close')
      request.setResponseCode(500, str(err))
      return "<html><h1>ERROR:</h1>\n<pre>%s</pre></html>" % (traceback.format_exc())

class UpdateManager(Resource):
  isLeaf = True
  clients = {}
  reference = None

  @report(category="UpdateManager")
  def __init__(self):
    UpdateManager.reference=self

  @report("UpdateManager")
  def timeout(self, connection, address):
    log.msg("UpdateManager.timeout (%s, %s)" % ( connection, address ))
    connection.write(json.dumps({"result": "timeout"}))
    connection.finish()
    if address in UpdateManager.reference.clients:
      if connection in UpdateManager.reference.clients[address]:
        UpdateManager.reference.clients[address].remove(connection)

  @classmethod
  @report(category="UpdateManager")
  def propagate(klass, address, args):
    if not klass.reference:
      return

    if not address in klass.reference.clients:
      return

    if "address" not in args:
      args["address"] = address

    for r in klass.reference.clients[address]:
      try:
        r.write(json.dumps(args))
        r.finish()
        r.delayed.cancel()
      except Exception, err:
        log.err(err)
    klass.reference.clients.pop(address)

  @report(category="UpdateManager")
  def lost_connection(self, err, address, request):
    log.msg("updateManager.lost_connection(%s, %s)" % (address, request))
    request.delayed.cancel()
    if address in self.clients:
      if request in self.clients[address]:
        self.clients[address].remove(request)

  @report(category="UpdateManager")
  def render_POST(self, request):
    address = request.args["address"][0]
    if address not in self.clients:
      self.clients[address] = []
    self.clients[address].append(request)
    request.delayed = reactor.callLater(60, self.timeout, connection=request, address=address)
#    request.delayed.addErrback(log.err)
    request.notifyFinish().addErrback(self.lost_connection, address=address, request=request)
    request.setHeader('Content-Type', 'application/json')
    request.setHeader('Cache-Control', 'no-cache')
    request.setHeader('Connection', 'close')
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
    self.putChild("scan", ScanManager())
    self.putChild("devices", DevicesManager())
    self.putChild("connected", ConnectionManager())
    self.putChild("configure", ConfigurationManager())
    self.putChild("doconfigure", doConfiguration())
    self.putChild("disconnect", DisconnectManager())
    self.putChild("updates", UpdateManager())
    self.putChild("switchstate", StateManager())

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
