# -*- coding: utf-8 -*-
import os
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
    zip_safe=False,
)
