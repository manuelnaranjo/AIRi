#!/bin/bash

set -ex

rm -rf ../temp
mkdir ../temp
pushd ../temp
cp -H -L -r ../python/* .

python2.6 -OO -m compileall *
find . -type f -iname \*.py -delete
find . -type f -iname \*.pyc -delete
zip -r ../deps/python.egg *
popd
rm -rf ../temp
