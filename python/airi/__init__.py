# -*- coding: utf-8 -*-
try:
    from twisted.internet import glib2reactor
    glib2reactor.install()
except:
    pass

from twisted.python import log
import logging

ENTRY   = 10
ARGS    = 20
RESULT  = 30

class report:
  """
  Decorator that prints information about function calls.
  Based on: http://paulbutler.org/archives/python-debugging-with-decorators/
  """

  def __init__(self, level=ENTRY, category=None):
    self.level=level
    self.category = category

  def __call__(self, fn):
    def wrap(*args, **kwargs):
      if self.level >= ARGS:
        fc="call to %s.%s (%s,%s)" % (
          fn.__module__, fn.__name__,
          ', '.join( [ repr(a) for a in args ] ),
          ', '.join( ["%s = %s" % (a, repr(b)) for a,b in kwargs.items()] )
        )
        log.msg(fc, level=logging.DEBUG, category=self.category)
      elif self.level >= ENTRY:
        log.msg("call to %s.%s" % (fn.__module__, fn.__name__), category=self.category, level=logging.DEBUG)

      ret = fn(*args, **kwargs)
      if self.level >= RESULT:
        log.msg("%s returned %s" % (fc, ret), level=logging.DEBUG)
      return ret
    if self.level > 0:
      return wrap
    return fn

__version__ = ('1', '0', 'c3')
__version__ = '.'.join(__version__)

import camera
from camera import dbg, CameraProtocol
import settings
import twisted_bluetooth
import stream
import server
import api
