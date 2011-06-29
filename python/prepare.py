#!/bin/env python

'''
This script will download all the required packages (js and css mostly) so you
can build properly the AIRi package.
'''

import urllib, os, os.path, zipfile

os.system("mkdir -p deps")

DEPS = {}

def add_dependency(package, base, version=None, extension="tar.gz", 
	urlformat="%(base)s/%(version)s/%(package)s-%(version)s.%(extension)s",
	filename="deps/%(package)s-%(version)s.%(extension)s"):
    DEPS[package]={
	'base': base,
	'package': package,
	'version': version,
	'extension': extension,
	'urlformat': urlformat,
	'fileformat': filename,
    }
    DEPS[package]['url']=urlformat%DEPS[package]
    DEPS[package]['filename']=filename%DEPS[package]

def download(package):
    pack = DEPS[package]
    os.system("wget -O %(filename)s %(url)s" % pack)

def uncompressJQueryMobile():
    def uncompress(opath, tpath):
	c=zipf.open(opath)
	os.system("mkdir -p %s" % os.path.dirname(tpath))
	o=file(tpath, "wb")
	o.write(c.read())
	o.close()
	c.close()

    filename = DEPS["jquery.mobile"]["filename"]
    version  = DEPS["jquery.mobile"]["version"]
    zipf = zipfile.ZipFile(filename)
    for f in zipf.filelist:
	if f.filename.endswith("jquery.mobile-%s.min.js" % version):
	    uncompress(f, "airi/media/js/jquery.mobile-%s.js" % version)
	elif f.filename.endswith("jquery.mobile-%s.min.css" % version):
	    uncompress(f, "airi/media/css/jquery.mobile-%s.css" % version)
	elif "images" in f.filename and f.filename.endswith("png"):
	    uncompress(f, "airi/media/css/images/%s" % f.filename.split(os.path.sep)[-1])

def main():
    add_dependency('jquery.mobile', 
	base='http://code.jquery.com/mobile',
	version='1.0b1',
	extension='zip')

    add_dependency('jquery',
	base='http://code.jquery.com/',
	version='1.6.1.min',
	extension='js',
	urlformat="%(base)s/%(package)s-%(version)s.%(extension)s",
	filename="airi/media/js/%(package)s-%(version)s.%(extension)s"
    )
    add_dependency('jquery.mobile.tabs',
	base='https://github.com/groovetrain/jQuery.mobile-Tabs/raw/master/',
	version=None,
	extension='js',
	urlformat="%(base)s/%(package)s.%(extension)s",
	filename="airi/media/js/%(package)s.%(extension)s"
    )
    add_dependency('jQueryRotate',
	base="http://jqueryrotate.googlecode.com/files/",
	version="2.1",
	extension='js',
	urlformat="%(base)s/%(package)s.%(version)s.%(extension)s",
	filename="airi/media/js/%(package)s-%(version)s.%(extension)s"
    )
    add_dependency('toolbox.flashembed',
	base="https://raw.github.com/jquerytools/jquerytools/master/src/toolbox/",
	extension='js',
	urlformat="%(base)s/%(package)s.%(extension)s",
	filename="airi/media/js/%(package)s.%(extension)s"
    )

    for pack in DEPS:
	if not os.path.isfile(DEPS[pack]['filename']):
	    download(pack)
	else:
	    print DEPS[pack]['filename'], "found"

    uncompressJQueryMobile()

if __name__=='__main__':
    main()
