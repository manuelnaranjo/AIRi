#!/bin/bash

source build.sh
ant uninstall
adb install bin/AIRi-release.apk
adb shell am start -n net.aircable.airi/.ScriptActivity
