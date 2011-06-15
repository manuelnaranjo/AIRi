#!/bin/bash

source build-debug.sh
adb uninstall net.aircable.airi
adb install bin/AIRi-debug.apk
adb shell am start -n net.aircable.airi/.ScriptActivity
