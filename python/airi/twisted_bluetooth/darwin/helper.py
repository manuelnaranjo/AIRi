# -*- coding: utf-8 -*-
# Copyright (c) 2011 Naranjo Manuel Francisco <manuel@aircable.net>
# Copyright (c) 2001-2009 Twisted Matrix Laboratories.
# See Twisted LICENSE for details.

"""
This class is used for Mac OSx Bluetooth connections.
"""

# System Imports
import os, types, sys, operator, socket
import lightblue
import socket

from multiprocessing.connection import Client

def main():
    pipe = Client(sys.argv[1])
    proto, target = pipe.recv()

    try:
        s = lightblue.socket(proto)
        s.connect(target)
        s.settimeout(1/100.)
        pipe.send(None)
        while True:
            if pipe.poll():
                b = pipe.recv()
                print "sending", b
                s.send(b)
            try:
                o = s.recv(4096)
                pipe.send(o)
            except Exception, err:
                pass

    except Exception, err:
        pipe.send(err)
        raise

if __name__=='__main__':
    if len(sys.argv) < 2:
        print "Usage %s <socket>" % sys.argv[0]
        sys.exit(1)
    main()

