set -x 
set -e

if [ -f res/raw/python.egg ]; then
  rm res/raw/python.egg
fi

pushd python
bash compress.sh
popd

ant clean
ant debug
adb uninstall net.aircable.airi
adb install bin/AIRi-debug.apk
adb shell am start -n net.aircable.airi/.ScriptActivity
