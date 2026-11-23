#!/usr/bin/env bash
set +e
mkdir -p tmp/offline-test
timeout 45s adb wait-for-device > tmp/offline-test/wait-device.txt 2>&1
adb uninstall com.ruirui.cjjlq > tmp/offline-test/uninstall.txt 2>&1
timeout 90s adb install -r dist/super-spirit-ball-offline.apk > tmp/offline-test/install.txt 2>&1
RC=$?
echo "$RC" > tmp/offline-test/install.exitcode
if [ "$RC" -ne 0 ]; then
  timeout 20s adb logcat -d -v threadtime > tmp/offline-test/logcat-install-failed.txt
  exit 1
fi
# Disable emulator networking before the app is opened.
adb shell svc wifi disable > tmp/offline-test/disable-wifi.txt 2>&1
adb shell svc data disable > tmp/offline-test/disable-data.txt 2>&1
adb shell settings put global airplane_mode_on 1
adb shell am broadcast -a android.intent.action.AIRPLANE_MODE --ez state true > tmp/offline-test/airplane.txt 2>&1
adb shell monkey -p com.ruirui.cjjlq -c android.intent.category.LAUNCHER 1 > tmp/offline-test/launch.txt 2>&1
sleep 120
timeout 20s adb shell screencap -p /sdcard/offline-game-screen.png
timeout 30s adb pull /sdcard/offline-game-screen.png tmp/offline-test/offline-game-screen.png > /dev/null 2>&1
timeout 20s adb shell uiautomator dump /sdcard/offline-ui.xml > tmp/offline-test/ui-dump.txt 2>&1
timeout 20s adb pull /sdcard/offline-ui.xml tmp/offline-test/ui.xml > /dev/null 2>&1
timeout 20s adb shell dumpsys activity activities > tmp/offline-test/activities.txt 2>&1
timeout 20s adb shell dumpsys window windows > tmp/offline-test/windows.txt 2>&1
timeout 20s adb shell pidof com.ruirui.cjjlq > tmp/offline-test/app-pid.txt 2>&1
timeout 30s adb logcat -d -v threadtime > tmp/offline-test/logcat.txt
{
  echo "=== install ==="
  cat tmp/offline-test/install.txt
  echo "=== app pid ==="
  cat tmp/offline-test/app-pid.txt
  echo "=== Offline H5 log lines ==="
  grep -iE "\\[Offline\\]|offline patch|local LoginRsp|EnterSceneRsp|file:///android_asset/game|ERR_FILE_NOT_FOUND|FATAL EXCEPTION|Uncaught" tmp/offline-test/logcat.txt | tail -n 600 || true
  echo "=== network errors ==="
  grep -iE "ERR_INTERNET_DISCONNECTED|ERR_NAME_NOT_RESOLVED|UnknownHost|网络不可用" tmp/offline-test/logcat.txt | tail -n 200 || true
} > tmp/offline-test/SUMMARY.txt
cat tmp/offline-test/SUMMARY.txt
if grep -q "local LoginRsp" tmp/offline-test/logcat.txt && grep -q "EnterSceneRsp" tmp/offline-test/logcat.txt; then
  echo "OFFLINE_SCENE_TEST=PASS" | tee -a tmp/offline-test/SUMMARY.txt
  exit 0
fi
echo "OFFLINE_SCENE_TEST=FAIL (LoginRsp/EnterSceneRsp markers missing)" | tee -a tmp/offline-test/SUMMARY.txt
exit 1
