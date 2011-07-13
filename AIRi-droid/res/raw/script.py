#!/usr/bin/env python 
# -*- coding: utf-8 -*-

import sys, imp, os
from android import API
from os import path, listdir
droid = API()

class stdout():
    def __init__(self):
        self.f = file(
            os.path.join(os.environ["EXTERNAL_STORAGE"], "airi.log"),
            "wb")
        self.stdout = sys.stdout
        self.stderr = sys.stderr

    def write(self, what):
        droid.log(what)
        self.f.write(what)
        self.f.flush()
        self.stdout.write(what)

    def writelines(self, lines):
        for l in lines:
           droid.log(l)
        self.stdout.writelines(lines)
        self.f.writelines(what)
        self.f.flush()

    def __getattr__(self, name):
        #droid.log("stdout get %s" % name)
        return getattr(self.stdout, name)

def createSymbolicLinks(files):
    print "createSymbolicLinks"
    libs=os.path.join(path.dirname(parent), "lib")
    A=open(os.path.join(parent, "filelist.txt"), "r")
    for l in A.readlines():
        if len(l.split()) < 2:
            continue
        src,dest=l.split()
        src,dest=[os.path.join(libs, src), os.path.join(files, dest)]
        print dest, "->", src,
        if os.path.islink(dest):
            print "skipped"
            continue
        if os.path.exists(dest):
            os.remove(dest)
        os.symlink(src, dest)
        print "created"

out = stdout()
sys.stdout = out
sys.stderr = out

try:
    parent = path.dirname(path.realpath(__file__))
    createSymbolicLinks(parent)
    sys.path.pop(0)
    sys.path.insert(0, path.join(parent,"python.egg"))
    [ sys.path.insert(1, path.join(parent,i)) for i in listdir(parent) if i.endswith("egg") ]

    import pkg_resources
    pkg_resources.set_extraction_path(parent)

    os.environ["DATA_PATH"]=parent

    from airidroid import main
    main()

except Exception, err:
    import traceback
    droid.makeToast(str(err))
    droid.log(str(err))
    traceback.print_exc(file=out)

out.f.close()
