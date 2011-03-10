# -*- coding: utf-8 -*-
#    AIRi
#    Copyright (C) 2011
#

from lxml import etree
from re import compile
from exceptions import IOError
import os
from logging import root as logger

VALID_ADDRESS=compile("([0-9a-f]{2}\:){5}([0-9a-f]{2})")

DEFAULT='''<xml>
<cameras>
</cameras>
<dongles>
</dongles>
<debug>False</debug>
</xml>'''

class XMLTool:
    """
    """

    def __init__(self, xmlfile=None):
        if xmlfile == None:
          xmlfile = os.path.join([os.path.realpath(__file__), "airi-settings.xml"])
        self.__file = xmlfile
        self.tree = None

    def __getXmlTree(self):
        """ Open an xml file and return an etree xml instance or None
        """
        self.tree = etree.parse(self.__file)
        if self.tree is None:
            raise Exception("no config file")

    def __sanitize(self):
        try:
            if self.tree is None:
                self.__getXmlTree()
        except Exception, err:
            print err
            self.tree=etree.fromstring(DEFAULT)

    def __getValueOrDefault(self, key, default):
        self.__sanitize()
        try:
            return self.tree.xpath(key)[0].text
        except:
            # if we got here then it's quite possible there's no 
            # setting defined in the xml
            return default

    #persistance methods
    def getAllSettings(self):
        return {
            'dongles': self.getAllDongleSettings(),
            'cameras': self.getAllCameraSettings(),
            'debug':   self.isDebugEnabled(),
        }

    def genXML(self, settings, indent=1, header="xml"):
        out = ""
        if header:
            out+="<%s>\n" % header
        for key, value in settings.iteritems():
            for i in range(indent):
                out+="\t"
            out+="<%s>" % key
            if type(value) is dict:
                out+="\n%s\n" % self.genXML(value, indent+1, None)
                for i in range(indent):
                    out+="\t"
                out+="</%s>\n" % key

            else:
                out+=str(value)
                out+="</%s>\n" % key
        if header:
            out+="</%s>" % header

        return out

    def saveSettings(self, settings):
        out = file(self.__file, 'w')
        out.write(self.genXML(settings))
        out.close()

    # generic functions
    def getValueOrDefault(self, key, default=None):
        """Generic return function"""
        return self.__getValueOrDefault(key, default)

    def getDict(self, parent, default={}):
        """Generic access to dict values"""
        self.__sanitize()
        key = self.tree.findall(parent)
        if len(key) > 0:
            return self.__todict(key[0], False)
        return default

    # debug staff
    def isDebugEnabled(self, default="true"):
        """Return debug preference as configured in xxx.xml
        """
        debug = self.__getValueOrDefault('debug', default)
        return debug.lower() == "true"

    # dongle stuff ...
    def getAllDongleSettings(self):
        try:
            self.__sanitize()
            blocks = self.tree.findall('dongle/block')
            out = dict()
            for block in blocks:
                addr = block.find('address').text
                out[addr]=self.__todict(block)

            # back to default
            default = self.tree.findall('dongle/default')
            if len(default) > 0:
                out['default'] = self.__todict(default[0])
            return out
        except AttributeError, err:
            print err
            return {}
    
    def getDongleByAddress(self, address=""):
        if not VALID_ADDRESS.match(address.lower()):
            raise Exception("Not Valid Bluetooth Address %s" % address)
        try:
            self.__sanitize()

            blocks = self.tree.findall('dongle/block')
            for block in blocks:
                addr = block.find('address').text.lower()
                if address.lower().startswith(addr):
                    logger.info("%s passes filter %s" %( address, addr))
                    return self.__todict(block)

            # back to default
            default = self.tree.findall('dongle/default')
            if len(default) > 0:
                block = default[-1]
                return self.__todict(block)
        except AttributeError:
          pass

        # not even default settings
        return {"enabled": True}

    # camera stuff ...
    def getAllCameraSettings(self):
        try:
            self.__sanitize()
            blocks = self.tree.findall('camera/block')
            out = dict()
            for block in blocks:
                addr = block.find('address').text
                out[addr]=self.__todict(block)

            # back to default
            default = self.tree.findall('camera/default')
            if len(default) > 0:
                out['default'] = self.__todict(default[0])
            return out
        except AttributeError:
            return {}
    
    def getCameraByAddress(self, address=""):
        if not VALID_ADDRESS.match(address.lower()):
            raise Exception("Not Valid Bluetooth Address %s" % address)
        try:
            self.__sanitize()

            blocks = self.tree.findall('camera/block')
            for block in blocks:
                addr = block.find('address').text.lower()
                if address.lower().startswith(addr):
                    logger.info("%s passes filter %s" %( address, addr))
                    return self.__todict(block)

            # back to default
            default = self.tree.findall('camera/default')
            if len(default) > 0:
                block = default[-1]
                return self.__todict(block)

            # not even default settings
            return {}

        except AttributeError:
            return {}


    def __todict(self, block, ignore_address=True):
        out = dict()
        for children in list(block):
            if children.tag!='address' or not ignore_address:
                if len(list(children)) > 0:
                    out[children.tag] = self.__todict(children, ignore_address)
                else:
                    out[children.tag]=children.text
        return out

if __name__ == '__main__':
    print "using foo2.xml"
    xt = XMLTool("foo2.xml")

    print '00:50:C2:00:00:02', xt.getDongleByAddress('00:50:C2:00:00:02')
    print 'f4:AA:BB:00:00:06', xt.getDongleByAddress('f4:AA:BB:00:00:06')
    print '00:50:C2:00:00:02', xt.getCameraByAddress('00:50:C2:00:00:02')
    set = xt.getAllSettings()
    print set
    print xt.genXML(set)

