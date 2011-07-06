#!/usr/bin/env python
# -*- coding: utf-8 -*-
from airi.jinja import main as jmain
from twisted.internet import reactor
from twisted.python import log
import sys

def browser_ready():
    if 'win' in sys.platform:
        return True
    from subprocess import Popen, PIPE
    try:
        p = Popen(["xset", "-q"], stdout=PIPE, stderr=PIPE)
        p.communicate()
        return p.returncode == 0
    except:
        return False

def startbrowser():
    import webbrowser
    print "Starting up browser"
    webbrowser.open("http://localhost:8000")

def main():
    import sys
    if sys.platform == "linux2":
        from pair import main
        reactor.callWhenRunning(main)
    log.startLogging(sys.stdout)
    nobrowser = "--nobrowser" in sys.argv
    if nobrowser:
        sys.argv.remove("--nobrowser")
    if len(sys.argv) > 1:
        jmain(int(sys.argv[1]))
    else:
        jmain()
    if browser_ready() and not nobrowser:
        import webbrowser
        reactor.callLater(1, startbrowser)
    reactor.run()

if __name__ == '__main__':
    main()
