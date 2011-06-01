# -*- coding: utf-8 -*-
import os, sys
from setuptools import setup, find_packages
from airi import __version__


def read(fname):
    '''
    Utility function to read the README file.
    Used for the long_description.  It's nice, because now 1) we have a top
    level README file and 2) it's easier to type in the README file than to put
    a raw string in below
    '''
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

REQUIRES = [
    "Twisted >= 11.0.0",
    "Jinja2"
]

if sys.platform.startswith("linux") or sys.platform.startswith("win"):
    REQUIRES.append("PyBluez >= 0.18")
elif sys.platform.startswith("darwin"):
    REQUIRES.append("lightblue >=0.4")

setup(name="airi",
    version=__version__,
    author="Naranjo Manuel Francisco",
    author_email="manuel@aircable.net",
    description=("AIRi software package"),
    license="Apache V2",
    keywords="airi bluetooth twisted",
    url="https://github.com/manuelnaranjo/AIRi",
    packages=find_packages("."),
    long_description=read('README'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Environment :: Web Environment",
        "Framework :: Twisted",
        "Topic :: Communications",
        "Topic :: Multimedia :: Video :: Capture",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
    ],
    include_package_data=True,
    package_data={
      'airi': ['airi/media/*.*', 'airi/templates/*.*'],
    },
    #scripts=["AIRi"],
    entry_points = {
      'console_scripts': [
        'AIRi = airi.main:main', 
      ]
    },
    dependency_links = [
	"http://code.google.com/p/pybluez/downloads/list",
	"http://prdownloads.sourceforge.net/lightblue/"
    ],
    install_requires = REQUIRES,
    zip_safe=False,
)
