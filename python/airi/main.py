#!/usr/bin/env python
# -*- coding: utf-8 -*-
from airi.jinja import main as jmain
from twisted.internet import reactor
from twisted.python import log

def main():
	import sys
	if sys.platform == "linux2" and "-nopairing" not in sys.argv:
		from pair import main
		reactor.callWhenRunning(main)
	log.startLogging(sys.stdout)
	if len(sys.argv) > 1:
		jmain(int(sys.argv[1]))
	else:
		jmain()
	reactor.run()

if __name__ == '__main__':
	main()

