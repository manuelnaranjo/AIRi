import ConfigParser
from os import path, access, W_OK, environ

DEFAULTS={
  "dongles": {
    "default": True,
  },
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

    self.config = ConfigParser.SafeConfigParser()
    for section in DEFAULTS:
      if self._has_section(section):
        continue;

      self._add_section(section)
      for key, value in DEFAULTS[section].iteritems():
        self._set(section, key, str(value))

    if path.exists(name) and path.isfile(name):
      print "loading from", name
      self._read(name)

  def getDongle(self, address):
    address = address.replace(":", "_")
    dongles = self._options("dongles")
    for op in dongles:
      if address.lower().startswith(op):
        return self._getboolean("dongles", op)
    return self._getboolean("dongles", "default")

  def getCameraSections(self):
    cameras = self._sections()
    if "dongles" in cameras:
      cameras.remove("dongles")
    return cameras

  def getCameraSection(self, address, create=False):
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
      elif key in ['reconnect', 'enable', 'voice', 'flash']:
        out[key] = val.lower() == "true"
      else:
        out[key] = val
    return out

  def getCameras(self):
    for camera in self.getCameraSections():
      yield self.__cameraDict(self._items(camera))

  def getCamera(self, address):
    cam = self.getCameraSection(address)
    if cam:
      return self.__cameraDict(self._items(cam))
    return None

  def save(self):
    self._write(open(self.name, "wb"))

  def __sanitizeSetting(self, key, val):
    if key in ['reconnect_timeout', 'exposure']:
      val = int(val)
    elif key in ['reconnect', 'enable', 'voice', 'flash']:
      if type(val) != bool:
        val = val.lower() in ["true", "ok"]
    return str(val)

  def setCameraSetting(self, address, key, value, section=None):
    if not section:
      section = self.getCameraSection(address, True)
    if not value:
      self._remove_option(section, key)
    else:
      self._set(section, key, self.__sanitizeSetting(key, value))

  def setCamera(self, configuration):
    if "address" not in configuration:
      raise Exception("You need to set address")

    section = self.getCameraSection(configuration["address"], True)

    for key, value in configuration.iteritems():
      self.setCameraSetting(configuration["address"], key, value)
    self.save()

  def setDongle(self, block, enable=False):
    self._set("dongles", block.replace(":", "_"), str(enable))

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

