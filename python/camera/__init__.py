# -*- coding: utf-8 -*-
import logging
from twisted.python import log

def dbg(*a, **kw):
  kw["logLevel"] = logging.DEBUG
  log.msg(*a, **kw)

class CameraProtocol():
  def setSize(self, size):
    raise NotImplementedError()

  def getSize(self):
    raise NotImplementedError()

  def getSizes(self):
    raise NotImplementedError()

  def getCapabilities(self):
    raise NotImplementedError()

  def disconnect(self):
    dbg("CameraProtocol.disconnect not implemented")

class Listener():
  def lostConnection(self, reason, failed, *a, **kw):
    raise NotImplementedError()

  def gotFrame(self, frame, *a, **kw):
    raise NotImplementedError()

  def forcedDisconnect(self, *a, **kw):
    dbg("Listener.forcedDisconnect not implemented")
