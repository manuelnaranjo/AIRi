#!/usr/bin/env python 
# -*- coding: utf-8 -*-

import sys, imp, os
from android import API
from os import path, listdir
droid = API()

class stdout():
    def __init__(self):
        self.stdout = sys.stdout
        self.stderr = sys.stderr

    def write(self, what):
        droid.log(what)
        self.stdout.write(what)

    def writelines(self, lines):
        for l in lines:
           droid.log(l)
        self.stdout.writelines(lines)

    def __getattr__(self, name):
        #droid.log("stdout get %s" % name)
        return getattr(self.stdout, name)

out = stdout()
sys.stdout = out
sys.stderr = out

def start_browser(listener):
    droid.log(str(listener))
    droid.log("starting view in port %s" % listener._realPortNumber)
    droid.webViewShow("http://127.0.0.1:%s" % listener._realPortNumber)

try:
    parent = path.dirname(path.realpath(__file__))
    sys.path.pop(0)
    sys.path.insert(0, path.join(parent,"python.egg"))
    [ sys.path.insert(1, path.join(parent,i)) for i in listdir(parent) if i.endswith("egg") ]

    import pkg_resources
    pkg_resources.set_extraction_path(droid.environment()["appcache"])

    os.environ["DATA_PATH"]=parent

#    from rpyc_classic import main
    from airi.jinja import main
    droid.log("Starting server")
    l = main(port=0)
    from twisted.internet import reactor
    reactor.callWhenRunning(start_browser, listener=l)
    reactor.run()
except Exception, err:
    import traceback
    droid.log(str(err))
    traceback.print_exc(file=out)

