#!/bin/python

'''
AIRi install script
'''
import os, sys, subprocess

def downloadVirtualEnv():
    print "downloading virtualenv"
    import urllib2
    r = urllib2.urlopen("https://raw.github.com/pypa/virtualenv/develop/virtualenv.py")
    b=r.read()
    r.close()
    A=open("virtualenv.py", "wb")
    A.write(b)
    A.close()

try:
    import virtualenv
except:
    downloadVirtualEnv()
    import virtualenv

def getDefaultInstallationPath():
    def internalInstallationPath():
        if sys.platform.startswith("linux"):
            if os.access("/opt", os.W_OK):
                return "/opt"
            return os.path.expanduser("~")
        elif sys.platform.startswith("darwin"):
            if os.access("/Applications", os.W_OK):
                return "/Applications"
            return os.path.expanduser("~")
        elif sys.platform.startswith("win"):
            if os.access(os.environ["PROGRAMFILES"], os.W_OK):
                return os.environ["PROGRAMFILES"]
            return os.environ["APPDATA"]
        raise RuntimeError("Platform not supported")
    return os.path.join(internalInstallationPath(), "AIRi")

def getInstallationPath():
    default = getDefaultInstallationPath()
    r = raw_input("Do you want to install AIRi on %s [Y/n]? " % default)
    if r.lower().strip().startswith("y") or len(r.strip())==0:
        return default
    p = raw_input("Please type in install path: ").strip()
    if len(p) == 0:
        raise RuntimeError("Path can't be empty!")
    return p

def dohelp():
    print "Usage: %s --path path [install|update|remove]" % sys.argv[0]
    sys.exit(0)

def install(bin_):
    print "Creating virtualenv"
    virtualenv.main()
    print "Installing AIRi with dependencies"
    subprocess.call([os.path.join(bin_, "pip"), "install", "AIRi"])

def upgrade(bin_):
    print "Upgrading AIRi"
    subprocess.call([os.path.join(bin_, "easy_install"), "-U", "AIRi"])

def main():
    path = None
    method = None
    i = 0
    if "--path" in sys.argv:
        path = sys.argv[sys.argv.index("--path")+1]
    if "--help" in sys.argv:
        dohelp()

    method = sys.argv[-1].lower().strip()
    if method not in ["install", "update", "remove"]:
        dohelp()

    if method == "install":
        if not path:
            try:
                path = getInstallationPath()
            except KeyboardInterrupt:
                sys.exit(1)
    else:
        if not hasattr(sys, "real_prefix"):
            print "Need to be called from a virtualenv"
            sys.exit(0)
        path = sys.prefix
    print "Doing", method, "in", path

    if method=="remove":
        from twisted.python.filepath import FilePath
        FilePath(path).remove()
        sys.exit(0)

    sys.argv=sys.argv[:1]
    sys.argv.append(path)
    bin_ = virtualenv.path_locations(path)[-1]
    if method == "install":
        install(bin_)
    if not os.path.isdir(os.path.join(path, bin_)):
        print "You need to run install first!"
        sys.exit(1)
    upgrade(bin_)
    print "Run AIRi:", os.path.join(path, bin_, "AIRi")
    print "Handle AIRi package:", os.path.join(path, bin_, "AIRi-setup")

if __name__=='__main__':
    main()
