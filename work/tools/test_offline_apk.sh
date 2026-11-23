#!/usr/bin/env bash
set +e
mkdir -p tmp/offline-test
adb wait-for-device
adb uninstall com.ruirui.cjjlq > tmp/offline-test/uninstall.txt 2>&1
adb install -r dist/super-spirit-ball-offline.apk > tmp/offline-test/install.txt 2>&1
RC=$?
echo "$RC" > tmp/offline-test/install.exitcode
if [ "$RC" -ne 0 ]; then
  adb logcat -d -v threadtime > tmp/offline-test/logcat-install-failed.txt
  exit 0
fi
# Disable emulator networking before the app is opened.
adb shell svc wifi disable > tmp/offline-test/disable-wifi.txt 2>&1
adb shell svc data disable > tmp/offline-test/disable-data.txt 2>&1
adb shell settings put global airplane_mode_on 1
adb shell am broadcast -a android.intent.action.AIRPLANE_MODE --ez state true > tmp/offline-test/airplane.txt 2>&1
adb shell monkey -p com.ruirui.cjjlq -c android.intent.category.LAUNCHER 1 > tmp/offline-test/launch.txt 2>&1
sleep 120
adb shell screencap -p /sdcard/offline-game-screen.png
adb pull /sdcard/offline-game-screen.png tmp/offline-test/offline-game-screen.png > /dev/null 2>&1
adb shell uiautomator dump /sdcard/offline-ui.xml > tmp/offline-test/ui-dump.txt 2>&1
adb pull /sdcard/offline-ui.xml tmp/offline-test/ui.xml > /dev/null 2>&1
adb shell dumpsys activity activities > tmp/offline-test/activities.txt 2>&1
adb shell dumpsys window windows > tmp/offline-test/windows.txt 2>&1
adb shell pidof com.ruirui.cjjlq > tmp/offline-test/app-pid.txt 2>&1
adb logcat -d -v threadtime > tmp/offline-test/logcat.txt
adb root > tmp/offline-test/adb-root.txt 2>&1
adb wait-for-device
adb pull /data/user/0/com.ruirui.cjjlq tmp/offline-test/app-data 2> tmp/offline-test/app-data-pull.txt
{
  echo "=== install ==="
  cat tmp/offline-test/install.txt
  echo "=== app pid ==="
  cat tmp/offline-test/app-pid.txt
  echo "=== Offline H5 log lines ==="
  grep -iE "\[Offline\]|offline patch|local LoginRsp|EnterSceneRsp|file:///android_asset/game|ERR_FILE_NOT_FOUND|FATAL EXCEPTION|Uncaught" tmp/offline-test/logcat.txt | tail -n 500 || true
  echo "=== external request hints ==="
  grep -iE "httpCmd|cjjlq|UnknownHost|ERR_INTERNET_DISCONNECTED|ERR_NAME_NOT_RESOLVED" tmp/offline-test/logcat.txt | tail -n 200 || true
} > tmp/offline-test/SUMMARY.txt
cat tmp/offline-test/SUMMARY.txt
exit 0
