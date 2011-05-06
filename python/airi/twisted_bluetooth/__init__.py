# -*- coding: utf-8 -*-
import sys

if sys.platform.startswith("linux"):
    from bluez import *
elif sys.platform.startswith("win"):
    from win import *
elif sys.platform.startswith("darwin"):
    from darwin.sock import *
else:
    raise Exception, "Platform not supported"

