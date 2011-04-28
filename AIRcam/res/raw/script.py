#!/usr/bin/env python 
# -*- coding: utf-8 -*-

import sys, imp, os
from android import API
from os import path
droid = API()

parent = path.dirname(path.realpath(__file__))
sys.path.pop(0)
sys.path.insert(0, path.join(parent,"python.zip"))
sys.path.insert(1, path.join(parent,"pybluez.egg"))

import pkg_resources
pkg_resources.set_extraction_path(droid.environment()["appcache"])

os.environ["DATA_PATH"]=parent

try:
  import bluetooth
  import main
except Exception, err:
  from android import API
  from traceback import format_exc
  API().log(str(err))
  API().log(format_exc())
  import time
  time.sleep(10)
