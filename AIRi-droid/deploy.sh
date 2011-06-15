#!/bin/bash

source build.sh
adb uninstall net.aircable.airi
adb install bin/AIRi-release.apk
adb shell am start -n net.aircable.airi/.ScriptActivity
