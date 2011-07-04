#!/bin/bash

set -x 
set -e

mkdir -p deps

if [ -f deps/python.egg ]; then
  rm deps/python.egg
fi

pushd res/raw
python -m compileall . .
find . -iname \*.pyc -type f -delete
popd

pushd python
bash compress.sh
popd

rm -rf temp
rm -rf out
mkdir out
mkdir temp
pushd temp
if [ -f ../deps/all.egg ]; then
    rm ../deps/all.egg
fi
for i in $(ls ../deps/*.egg); do
    unzip -o ../deps/$i
done
for i in $(find . -iname test -type d); do
    rm -rf $i
done
python2.6 -OO -m compileall *
find . -iname \*.py -type f -delete
zip -r ../out/all.egg *
popd
rm -rf temp

rm res/raw/filelist.txt
touch res/raw/filelist.txt

COUNT=0
for i in $(ls out); do
    cp out/$i libs/armeabi/lib_airi_$COUNT.so
    echo "lib_airi_$COUNT.so $i" >> res/raw/filelist.txt
    ((COUNT = COUNT + 1 ))
    echo $COUNT
done
rm -rf out

ant clean
