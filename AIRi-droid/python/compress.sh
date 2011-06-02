#!/bin/bash

set -ex

python -m compileall *.py airi
find . -type f -iname \*.pyc -delete

zip -r ../res/raw/python.egg *
