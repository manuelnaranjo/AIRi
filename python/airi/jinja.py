# -*- coding: utf-8 -*-
from twisted.web.resource import Resource
from twisted.python import log
from twisted.web.static import File
from jinja2 import Environment, PackageLoader
from airi import __version__
from airi.camera.protocol import CameraFactory
from airi.camera import UnknownDevice
from airi.settings import getSettings
from airi.twisted_bluetooth import resolve_name
from airi.stream import StreamResource
from airi.sco import SCOResource
import airi.twisted_bluetooth as bluetooth
import pkg_resources, os, time

settings = getSettings()

class TemplateResource():
    def __init__(self, template, context):
        self.template = template
        self.context = context

    def render(self, *args, **kwargs):
        return str(self.template.render(self.context))

class Main(Resource):
    isLeaf = False

    def __init__(self, home="/"):
        Resource.__init__(self)
        self.env = Environment(loader=PackageLoader("airi", "templates"))
        self.env.globals["home"]=home

    def index(self, request):
        devices = list(CameraFactory.getCameras())
        for dev in devices:
            dev["viewers"] = StreamResource.getClients(dev["address"])
        return {
          "devices": devices 
        }

    def setup(self, request):
        def saveCamera(args):
            if "enable_pincode" in args:
                if args["enable_pincode"][0].lower()=="true":
                    settings.setPIN(block=args["address"][0],
                          npin=args["pincode"][0])
                else:
                    settings.delPIN(args["address"][0])
            settings.save()
            for k in ["save", "last", "battery", "status",
                            "enable_pincode", "pincode", "new-device"]:
                if k in args:
                    args.pop(k)
            for k in args.keys():
                args[k]=args[k][0]
            print "saving camera", args
            settings.setCamera(args)
            settings.save()

        def deleteCamera(address):
            settings.deleteCamera(address)
            settings.save()

        def getCamera(address):
            out = {}
            try:
                out.update(CameraFactory.getCamera(address))
            except UnknownDevice, err:
                out["address"] = address
                out["name"] = resolve_name(address)
                out["new_device"] = True
                out["types"] = CameraFactory.getTypes()
            return out

        if "address" not in request.args:
            raise Exception("Invalid address")

        address = request.args["address"][-1]

        if request.method == "POST":
            if "save" in request.args:
                saveCamera(request.args)
            if "delete" in request.args:
                deleteCamera(address)
        return getCamera(address)

    def scan(self, request):
        try:
            log.msg("Doing scan")
            cache = bluetooth.discover_devices(lookup_names=True)
            log.msg(cache)
            out = {"devices":
                    [{
                      'address':x[0],
                      'name':x[1],
                      'state': CameraFactory.isConnected(x[0])
                    }
                        for x in cache
                    ]
                }
            log.msg(out)
            return out
        except Exception, err:
            log.err(err)
            return {"error": str(err)}

    def server_setup(self, request):
        if request.method == "POST":
            if "delete" in request.args:
                settings.delPIN(request.args["delete"][0])
                settings.save()
            elif "save" in request.args:
                request.args.pop("save")
                blocks = dict([ (b,request.args[b][0]) for b in request.args if b.startswith("block") ])
                pins = dict([ (b,request.args[b][0]) for b in request.args if b.startswith("value") ])
                sets = {}
                for b in blocks:
                    if len(blocks[b].strip()) == 0:
                        continue
                    settings.setPIN(block=blocks[b], npin=pins["value"+b.replace("block","")])
                settings.save()

        out = {}
        out["pins"]=settings.getPINs()
        return out

    def stream(self, request):
        if "address" not in request.args:
            raise Exception("You need to provide with an address")
        camera = CameraFactory.getCamera(request.args["address"][0], True)
        if camera["enable_pincode"]:
            camera["pincode"]="************"
        return {
          "isChrome": "chrome" in request.requestHeaders.getRawHeaders("user-agent")[0].lower(),
          "address": request.args["address"][0],
          "camera": camera
        }

    contexts = {
        "index.html": index,
        "setup.html": setup,
        "scan.html": scan,
        "server-setup.html": server_setup,
        "stream.html": stream
    }

    def getChild(self, path, request):
        if "media" in path or "favicon.ico" in path:
            return Resource.getChild(self, path, request)
        if len(path) == 0:
            path = "redirect.html"
        template = self.env.get_template(path)
        context = self.contexts.get(path, lambda x,y: {})(self, request)
        context["pairing_supported"]=bluetooth.isPairingSupported()
        context["l2cap_supported"]=bluetooth.L2CAP_SUPPORTED
        context["sco_supported"]=bluetooth.SCO_SUPPORTED
        context["version"] = __version__
        return TemplateResource(template, context)

def main(port=8000):
    from twisted.application.service import Application
    from twisted.application.internet import TCPServer
    from twisted.web.server import Site
    from twisted.internet import reactor
    from airi.api import API
    import sys
    log.startLogging(sys.stdout)

    MEDIA = pkg_resources.resource_filename("airi", "/media")
    FAVICON = pkg_resources.resource_filename("airi", "/media/favicon.ico")
    print "serving static content from", MEDIA

    root = Main()
    path = os.path.dirname(os.path.realpath(__file__))
    root.putChild("api",        API())
    root.putChild("media", File( MEDIA, defaultType=None ) )
    root.putChild("sco", SCOResource())
    root.putChild("stream", StreamResource())
    root.putChild("favicon.ico", File( FAVICON, defaultType=None) )
    p=reactor.listenTCP(port, Site(root), interface="0.0.0.0", backlog=5)
    return p

if __name__=='__main__':
    from twisted.internet import reactor
    main()
    reactor.run()

