# -*- coding: utf-8 -*-
from airi.server import site
from twisted.internet import reactor
from twisted.python import log

if __name__=='__main__':
  import sys
  log.startLogging(sys.stdout)
  reactor.listenTCP(8000, site, interface="0.0.0.0")
  reactor.run()
