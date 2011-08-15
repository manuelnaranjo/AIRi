"""
AIRi startup script compatible with twisted format
"""


from twisted.internet import reactor
from twisted.application import service, internet

PORT = 8000

import sys
if sys.platform == "linux2":
    from airi.pair import main
    reactor.callWhenRunning(main)

def getWebService():
    """
    Return a service suitable for creating an application object.
    """
    from airi.jinja import service
    return internet.TCPServer(PORT, service())

application = service.Application("AIRiServer")
getWebService().setServiceParent(application)

