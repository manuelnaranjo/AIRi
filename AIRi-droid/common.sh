#!/bin/bash

set -e

mkdir -p deps
PYTHON="$(which python2.6)"
CWD="$(pwd)"

pushd ../python
VNUMBER=$(python -c "import sys; a=sys.stderr; sys.stderr=sys.stdout; sys.stdout=a; import airi; print >> sys.stderr, airi.__version__")
popd

function makeAIRiEgg() {
    # this function will create an egg file with the latest AIRi available
    echo "Creating airi $VNUMBER egg"
    rm -rf "${CWD}/deps/airi-*-py2.6.egg" > /dev/null
    pushd "${CWD}/../python" > /dev/null
    ${PYTHON} setup.py bdist_egg --exclude-source-files  > /dev/null
    cp dist/airi-$VNUMBER-py2.6.egg "${CWD}/deps" > /dev/null
    popd
}

function compile() {
    # this function will take a fake egg file (twisted, bluez and zope)
    # will compile it with the proper python compiler (py4a is 2.6) and
    # will repackage without the source code
    echo "Compiling $1" 
    rm -rf * > /dev/null
    unzip -o $1 > /dev/null
    ${PYTHON} -OO -m compileall * > /dev/null
    find . -iname \*.py -type f -delete  > /dev/null
    for k in $(find . -iname test -type d); do
       rm -rf $k  > /dev/null
    done
    zip -r ../out/$(basename $1) * > /dev/null
}

if [ ! -f res/raw/filelist.txt ] || [ ! -f "${CWD}/deps/airi-$VNUMBER-py2.6.egg" ]; then
    if [ -f deps/python.egg ]; then
        rm deps/python.egg
    fi

    # Check if all the res/raw scripts don't have sintaxis errors
    echo "Compiling res/raw"
    pushd res/raw
    python -m compileall . . > /dev/null
    find . -iname \*.pyc -type f -delete
    popd

    makeAIRiEgg

    # Build egg file from extra things
    pushd python
    echo "Compiling python scripts"
    bash compress.sh
    popd

    # now compile and repackage all the pieces
    rm -rf temp
    rm -rf out
    mkdir out
    mkdir temp
    pushd temp
    for i in $(ls ../deps/*.egg); do
        if [[ "$i" =~ .*py2.6.* ]]; then
            # this egg file is ready to be used on Android, no need to recompile
            echo "Copying $i"
            cp $i ../out/$(basename $i)
        else
            compile $i
        fi
    done
    popd
    rm -rf temp

    rm -rf res/raw/filelist.txt
    touch res/raw/filelist.txt

    rm -rf libs/armeabi/lib_airi_*.so
    COUNT=0
    for i in $(ls out); do
        cp out/$i libs/armeabi/lib_airi_$COUNT.so
        echo "lib_airi_$COUNT.so $i" >> res/raw/filelist.txt
        ((COUNT = COUNT + 1 ))
    done
    rm -rf out
fi
