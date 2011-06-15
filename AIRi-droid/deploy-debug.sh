#!/bin/bash

source build-debug.sh
ant uninstall
adb install bin/AIRi-debug.apk
adb shell am start -n net.aircable.airi/.ScriptActivity
