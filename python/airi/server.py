# -*- coding: utf-8 -*-
from twisted.application.internet import TCPServer
from twisted.web.resource import Resource
from twisted.web.server import Site
from twisted.web import server
from twisted.web.static import File
from twisted.internet import reactor
from twisted.python import log
from twisted.web.util import Redirect
from airi.api import API
from airi.stream import StreamResource, MultiPartStream
from functools import partial
import os

__all__=['root', 'site']
path = os.path.dirname(os.path.realpath(__file__))

root = Resource()
root.putChild("api",        API())
root.putChild("media",      File(os.path.join(path, "media/")))
root.putChild("",           File(os.path.join(path, "media/devices.html")))
root.putChild("scan",       File(os.path.join(path, "media/scan.html")))
root.putChild("configure",  File(os.path.join(path, "media/configure.html")))
root.putChild("devices",    File(os.path.join(path, "media/devices.html")))
root.putChild("video",      File(os.path.join(path, "media/video.html")))
root.putChild("stream",     StreamResource())
site = Site(root)

if __name__=='__main__':
    import sys
    log.startLogging(sys.stdout)
    reactor.listenTCP(8000, site, interface="0.0.0.0")
    reactor.run()
