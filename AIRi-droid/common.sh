#!/bin/bash

set -x 
set -e

if [ -f res/raw/python.egg ]; then
  rm res/raw/python.egg
fi

pushd python
bash compress.sh
popd

ant clean
