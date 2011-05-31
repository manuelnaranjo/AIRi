import sys, os
from android import API
from airi.jinja import main as jmain
from twisted.internet import reactor
from airi.stream import MultiPartStream
droid = API()

# def androidTimeout(self):
    # '''
    # Gets called after 1 minute since we lost the last viewer connected
    # if no one got registered again then we exit android
    # '''
    # if len(MultiPartStream.clients):
        # droid.log("Still has clients we don't exit yet")
    # droid.log("time to exit")
    # loop.stop()
    # 
# oConnectionTimeout = MultiPartStream.connectionTimeout
# def connectionTimeout(self):
    # droid.log("Android http connection timeout")
    # oConnectionTimeout(self)
    # reactor.callLater(60, androidTimeout)

def start_browser(listener):
    droid.log(str(listener))
    droid.log("starting view in port %s" % listener._realPortNumber)
    droid.webViewShow("http://127.0.0.1:%s" % listener._realPortNumber)

def main():
    droid.log("Starting server")
    l = jmain(port=0)
    reactor.callWhenRunning(start_browser, listener=l)
    reactor.run()

