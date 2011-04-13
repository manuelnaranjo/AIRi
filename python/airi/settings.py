# -*- coding: utf-8 -*-
import ConfigParser
from os import path, access, W_OK, environ
from twisted.python import log
import logging
from airi import report

DEFAULTS={
  "dongles": {
    "default": True,
  },
  "pin": {
    "default": 1234,
  }
}

class Settings():
  instance = None

  def __init__(self, name=None):
    if not name:
      parent = ""
      if access(path.dirname(path.realpath(__file__)), W_OK):
        parent = path.dirname(path.realpath(__file__))
      else:
        if "HOME" in environ:
          parent = environ["HOME"]
        elif "HOMEPATH" in environ:
          parent = environ["HOMEPATH"]
      name=path.join(parent, ".AIRi")
    print "configuration file", name
    self.name = name
    self.reload()


  def reload(self):
    self.config = ConfigParser.SafeConfigParser()
    for section in DEFAULTS:
      if self._has_section(section):
        continue;

      self._add_section(section)
      for key, value in DEFAULTS[section].iteritems():
        self._set(section, key, str(value))

    if path.exists(self.name) and path.isfile(self.name):
      print "loading from", self.name
      self._read(self.name)

  # @report(debug=True)
  def getDongle(self, address):
    self.reload()
    address = address.replace(":", "_")
    dongles = self._options("dongles")
    for op in dongles:
      if address.lower().startswith(op):
        return self._getboolean("dongles", op)
    return self._getboolean("dongles", "default")

  # @report(debug=True)
  def getCameraSections(self):
    self.reload()
    cameras = self._sections()
    if "dongles" in cameras:
      cameras.remove("dongles")
    if "pin" in cameras:
      cameras.remove("pin")
    return cameras

  # @report(debug=True)
  def getCameraSection(self, address, create=False):
    self.reload()
    cameras = self.getCameraSections()
    for cam in cameras:
      if address.lower().startswith(self._get(cam, "address").lower()):
        return cam
    if create:
      cameras=self._sections()
      if "dongles" in cameras:
        cameras.remove("dongles")
      section="camera%i"%(len(cameras)+1)
      self._add_section(section)
      self._set(section, "address", address)
      return section
    return None
  
  # @report(debug=True)
  def __cameraDict(self, items):
    # defaults
    out = {
      "reconnect_timeout": 10,
      "reconnect": False,
      "voice": False,
      "flash": False,
      "exposure": 15,
      "pan": "none"
    }
    for key, val in items:
      if key in ['reconnect_timeout', 'exposure']:
        out[key] = int(val)
      elif key in ['reconnect', 'enable', 'voice', 'flash', "enable_pincode"]:
        out[key] = val.lower() == "true"
      else:
        out[key] = val
    try:
      out["pincode"] = self.getPIN(out["address"], perfect=True, silent=False)
      out["enable_pincode"] = True
    except Exception, err:
      log.err(err)
      out["enable_pincode"] = False
    return out

  # @report(debug=True)
  def getCameras(self):
    self.reload()
    for camera in self.getCameraSections():
      yield self.__cameraDict(self._items(camera))

  # @report(debug=True)
  def getCamera(self, address):
    self.reload()
    cam = self.getCameraSection(address)
    if cam:
      return self.__cameraDict(self._items(cam))
    return None

  # @report(debug=True)
  def save(self):
    self._write(open(self.name, "wb"))

  # @report(debug=True)
  def __sanitizeSetting(self, key, val):
    if key in ['reconnect_timeout', 'exposure']:
      val = int(val)
    elif key in ['reconnect', 'enable', 'voice', 'flash', "enable_pincode"]:
      if type(val) != bool:
        val = val.lower() in ["true", "ok"]
    return str(val)

  # @report(debug=True)
  def setCameraSetting(self, address, key, value, section=None):
    if not section:
      section = self.getCameraSection(address, True)
    if not value:
      self._remove_option(section, key)
    else:
      self._set(section, key, self.__sanitizeSetting(key, value))

  # @report(debug=True)
  def setCamera(self, configuration):
    if "address" not in configuration:
      raise Exception("You need to set address")

    section = self.getCameraSection(configuration["address"], True)

    for key, value in configuration.iteritems():
      self.setCameraSetting(configuration["address"], key, value)
    self.save()
    from airi.api import UpdateManager
    UpdateManager.propagate(configuration["address"], configuration)

  # @report(debug=True)
  def setDongle(self, block, enable=False):
    self._set("dongles", block.replace(":", "_"), str(enable))

  # @report(debug=True)
  def setPIN(self, npin, block="default"):
    self._set("pin", block.replace(":", "_"), str(npin))
    from airi.api import UpdateManager
    UpdateManager.propagate(block.replace(":", "_"), {"pin": npin})

  # @report(debug=True)
  def delPIN(self, block):
    self._remove_option("pin", block.replace(":", "_"))
    from airi.api import UpdateManager
    UpdateManager.propagate(block.replace(":", "_"), {"pin": None})

  # @report(debug=True)
  def getPINs(self):
    self.reload()
    if not self.config.has_section("pin"):
      pins = {"default": default}
    else:
      pins = dict((b[0].replace("_", ":"), b[1]) for b in self.config.items("pin"))
    return pins

  # @report(debug=True)
  def getPIN(self, address=None, perfect=False, default="1234", silent=True):
    self.reload()
    if not self.config.has_section("pin"):
      pins = {"default": default}
    else:
      pins = dict((b[0].lower(), b[1]) for b in self.config.items("pin"))
    if not address:
      log.msg("No address falling back to default", level=logging.DEBUG)
      return pins.get("default", default)
    address=address.replace(":", "_").lower()

    for block in pins:
      if not perfect:
        if address.startswith(block):
          return pins[block]
      else:
        if address == block:
          return pins[block]
    if not silent:
      raise Exception("PIN not provided")
    return pins.get("default", default)

  def __getattr__(self, name):
    return getattr(self.config, name[1:])

def getSettings(name=None):
  if Settings.instance:
    return Settings.instance
  Settings.instance = Settings(name)
  return Settings.instance

if __name__=='__main__':
  import logging
  logging.basicConfig(level=logging.DEBUG)
  logging.info("starting demo")
  s=Settings("test.ini")
  logging.info(s.getDongle("00:25:BF:11:22:33"))
  s.setDongle("00:25:BF", "false")
  logging.info(s.getDongle("00:25:BF:11:22:33"))
  logging.info(s.getCamera("00:25:BF:11:22:33"))
  logging.info(s.getCamera("00:25:BF:00:25:BF"))
  s.setCamera({"address": "00:25:BF:00:25:AA", "reconnect": True})
  s.save()

