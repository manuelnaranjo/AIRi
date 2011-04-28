# Copyright (C) 2009 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

__author__ = [
  'Damon Kohler <damonkohler@gmail.com>',
  'Naranjo Manuel Francisco <manuel@aircable.net>'
]

import collections
import json
import os
import socket
import sys

PORT = os.environ.get('AP_PORT')
HOST = os.environ.get('AP_HOST')
HANDSHAKE = os.environ.get('AP_HANDSHAKE')
Result = collections.namedtuple('Result', 'id,result,error')

class _Android(object):
  def __init__(self, addr=None, debug=False):
    if addr is None:
      addr = HOST, PORT
    self.conn = socket.create_connection(addr)
    self.client = self.conn.makefile()
    self.id = 0
    self.debug = debug
    if HANDSHAKE is not None:
      self._authenticate(HANDSHAKE)

  def _rpc(self, method, *args):
    data = {'id': self.id,
            'method': method,
            'params': args}
    request = json.dumps(data)
    if self.debug and method != "log" and not method.startswith("_"):
      self.log("call to %s, params: %s" % (method, args))

    self.client.write(request+'\n')
    self.client.flush()
    response = self.client.readline()
    self.id += 1
    result = json.loads(response)

    if self.debug and method != "log" and not method.startswith("_"):
      self.log(str(result))

    if result['error'] is not None:
      raise Exception(result['error'])
    # we want to expose the result, not our internals
    return result["result"]

  def __getattr__(self, name):
    def rpc_call(*args):
      return self._rpc(name, *args)
    return rpc_call

_Android.reference = None

def API(addr=None, debug=False):
  if _Android.reference == None:
    # make it singleton
    _Android.reference = _Android(addr, debug)
  return _Android.reference
