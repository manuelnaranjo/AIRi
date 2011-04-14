# -*- coding: utf-8 -*-
from twisted.web.resource import Resource
from twisted.python import log
from twisted.web.static import File
from jinja2 import Environment, PackageLoader
from airi.camera.protocol import CameraFactory
from airi.camera import UnknownDevice
from airi.settings import getSettings
from airi.twisted_bluetooth import resolve_name
import os
import bluetooth

settings = getSettings()

class TemplateResource():
  def __init__(self, template, context):
    self.template = template
    self.context = context

  def render(self, *args, **kwargs):
    return str(self.template.render(self.context))

class Main(Resource):
  isLeaf = False

  def __init__(self, home="/"):
    Resource.__init__(self)
    self.env = Environment(loader=PackageLoader("airi", "templates"))
    self.env.globals["home"]=home

  def index(self, request):
    return {
      "devices": CameraFactory.getCameras()
    }

  def setup(self, request):
    if request.method == "POST" and "save" in request.args:
      args = request.args.copy()
      new_device = "new-device" in args
      if args["enable_pincode"][0].lower()=="true":
        settings.setPIN(block=args["address"][0], npin=args["pincode"][0])
      else:
        settings.delPIN(args["address"][0])
      settings.save()

      for k in ["save", "last", "battery", "status", 
                                  "enable_pincode", "pincode", "new-device"]:
        if k in args:
          args.pop(k)
      for k in args.keys():
        args[k]=args[k][0]
      print "saving camera", args
      settings.setCamera(args)
      settings.save()

    out = {}
    if "address" not in request.args:
      raise Exception("Invalid address")
    address = request.args["address"][-1]
    try:
      out.update(CameraFactory.getCamera(address))
    except UnknownDevice, err:
      out["address"] = address
      out["name"] = resolve_name(address)
      out["new_device"] = True
      out["types"] = CameraFactory.getTypes()
    print out
    return out

  def scan(self, request):
    try:
      log.msg("Doing scan")
      cache = bluetooth.discover_devices(lookup_names=True)
      log.msg(cache)
      out = {"devices": 
                [{
                  'address':x[0],
                  'name':x[1],
                  'state': CameraFactory.isConnected(x[0])
                }
                    for x in cache
                ]
            }
      log.msg(out)
      return out
    except Exception, err:
      log.err(err)
      return {"error": str(err)}

  def server_setup(self, request):
    if request.method == "POST":
      if "delete" in request.args:
        settings.delPIN(request.args["delete"][0])
        settings.save()
      elif "save" in request.args:
        request.args.pop("save")
        blocks = dict([ (b,request.args[b][0]) for b in request.args if b.startswith("block") ])
        pins = dict([ (b,request.args[b][0]) for b in request.args if b.startswith("value") ])
        sets = {}
        for b in blocks:
          if len(blocks[b].strip()) == 0:
            continue
          settings.setPIN(block=blocks[b], npin=pins["value"+b.replace("block","")])
        settings.save()

    out = {}
    out["pins"]=settings.getPINs()
    return out

  def stream(self, request):
    if "address" not in request.args:
      raise Exception("You need to provide with an address")
    return {
      "isChrome": "chrome" in request.requestHeaders.getRawHeaders("user-agent")[0].lower(),
      "address": request.args["address"][0],
      "camera": CameraFactory.getCamera(request.args["address"][0], True)
    }

  contexts = {
    "index.html": index,
    "setup.html": setup,
    "scan.html": scan,
    "server-setup.html": server_setup,
    "stream.html": stream
  }

  def getChild(self, path, request):
    if "media" in path or "favicon.ico" in path:
      return Resource.getChild(self, path, request)

    if len(path) == 0:
      path = "index.html"
    template = self.env.get_template(path)
    return TemplateResource(template, self.contexts.get(path, lambda x: {})(self, request))


def main():
  from twisted.application.service import Application
  from twisted.application.internet import TCPServer
  from twisted.web.server import Site
  from twisted.internet import reactor
  from airi.stream import StreamResource
  from airi.api import API
  import sys
  log.startLogging(sys.stdout)

  root = Main()
  path = os.path.dirname(os.path.realpath(__file__))
  root.putChild("api",        API())
  root.putChild("media", File(os.path.join(path, "media/")))
  root.putChild("stream", StreamResource())
  reactor.listenTCP(8000, Site(root), interface="0.0.0.0", backlog=5)
  reactor.run()#!/usr/bin/env python


if __name__=='__main__':
  main()
