# -*- coding: utf-8 -*-
import socket as sk
import errno
from threading import Thread
import time
#import logging
#logging.logMultiprocessing = False
#logging.basicConfig(level=logging.DEBUG)
#logger = logging.getLogger()

class StreamServer():
    def __init__(self, interface, portnumber, droid=None):
	self.interface = interface
	self.portnumber = portnumber
	self.clientsockets = {}
	self.droid = droid

    def killChildrens(self):
        for client in self.clientsockets.itervalues():
            client.close()
        self.clientsockets.clear()
    
    def log(self, text):
	if self.droid:
	    self.droid.log(text)
    
    def stop(self):
        self.killChildrens()
        self.socket.close()

    def create_server_socket(self):
        self.log("Creating stream socket %s" % self.portnumber)
        s = sk.socket(sk.AF_INET, sk.SOCK_STREAM, 0)
        s.setsockopt(sk.SOL_SOCKET, sk.SO_REUSEADDR, 1)
        s.bind((self.interface, self.portnumber))
        s.setblocking(False)
        s.listen(128)
        self.log("Stream Server ready")
        self.socket = s

    def send_to_all(self, text, mimetype='text/plain'):
    	delete = []
    	for client in self.clientsockets:
    	    while 1:
    		try:
    		    s = self.clientsockets[client]
    		    s.sendall('--myboundary\r\n')
    		    s.sendall('Content-type: %s\r\n' % mimetype)
    		    s.sendall('Content-size: %s\r\n' % len(text))
    		    s.sendall('\r\n')
    		    s.sendall(text)
    		    s.sendall('\r\n')
    		    break
    		except sk.error, err:
    	    	    if err[0] not in (errno.EWOULDBLOCK, errno.EAGAIN):
        		self.log("%s:%s got disconnected" % client)
    			self.log(str(err))
    			s.close()
    			delete.append(client)
    			break
    		    time.sleep(.0001)
    	self.log("sent to %s clients" % (len(self.clientsockets)-len(delete)))
    	for d in delete:
    	    del self.clientsockets[d]

    def handle_connection(self, conn, remote):
      conn.setblocking(2)
      try:
        request = conn.recv(4096)
      except Exception, err:
        self.log(str(e))
        conn.close()
        return True
      conn.setblocking(0)
      if not request or len(request) == 0:
        self.log("no request")
        conn.close()
        return True
      self.log("request: %s" % request)
      request = request.splitlines()
      if len(request) == 0:
        self.log("invalid request")
        conn.close()
        return True
      command, url = request[0].split()[:2]
      if command.strip() != 'GET':
          conn.shutdown(sk.SHUT_RDWR)
          conn.close()
          return True

      if url.strip() != '/':
        conn.shutdown(sk.SHUT_RDWR)
        conn.close()
        return True

      self.log("Got a connection to the http stream, redirecting")
      host = ''
      for line in request:
        if line.find('Host')>-1:
    	    host=line.strip().split()[1].split(':', 1)[0]

      conn.sendall('HTTP/1.0 200 OK\r\n')
      conn.sendall('Content-type:multipart/x-mixed-replace; boundary=--myboundary\r\n')
      conn.sendall('\r\n')
      self.clientsockets[remote] = conn
      self.log("Connection ready for streamming")
      return True

    def wait_connection(self):
      while True:
        try:
            conn, remote = self.socket.accept()
            self.log("accepted")
            self.handle_connection(conn, remote)
        except sk.error, e:
            #logger.error(e)
            if e[0] not in (errno.EWOULDBLOCK, errno.EAGAIN):
        	self.log(str(e))
                raise
    	    return True
