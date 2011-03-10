# -*- coding: utf-8 -*-
from twisted.application.internet import TCPServer
from twisted.web.resource import Resource
from twisted.web.server import Site
from twisted.web import server
from twisted.web.static import File
from twisted.internet import reactor
from twisted.python import log
from twisted.web.util import Redirect
from api import API
from stream import StreamResource, MultiPartStream
from functools import partial

__all__=['root', 'site']

root = Resource()
root.putChild("api", API())
root.putChild("media", File("media/"))
root.putChild("", File("media/index.html"))
root.putChild("scan", File("media/scan.html"))
root.putChild("configure", File("media/configure.html"))
root.putChild("devices", File("media/devices.html"))
root.putChild("favicon.ico", File("media/favicon.ico"))
root.putChild("stream", StreamResource())
site = Site(root)

if __name__=='__main__':
    import sys
#    import webcam
#    webcam.init(False)
#    def sendFrame():
#        MultiPartStream.sendToClients(webcam.repeat().tostring(), "image/jpeg")
#        reactor.callLater(1/20., sendFrame)

    log.startLogging(sys.stdout)
    reactor.listenTCP(8000, site, interface="0.0.0.0")
#    reactor.callLater(0, sendFrame)
    reactor.run()
