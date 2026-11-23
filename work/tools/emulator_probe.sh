#!/usr/bin/env bash
set +e
mkdir -p tmp/probe/device
adb wait-for-device

adb shell getprop > tmp/probe/device/getprop.txt
adb shell getprop ro.product.cpu.abilist > tmp/probe/device/abis.txt
adb shell dumpsys webviewupdate > tmp/probe/device/webview-provider.txt 2>&1
adb install -r com.ruirui.cjjlq.apk > tmp/probe/device/install.txt 2>&1
INSTALL_RC=$?
echo "$INSTALL_RC" > tmp/probe/device/install.exitcode

if [ "$INSTALL_RC" -eq 0 ]; then
  adb shell pm dump com.ruirui.cjjlq > tmp/probe/device/package-dump.txt 2>&1
  adb shell monkey -p com.ruirui.cjjlq -c android.intent.category.LAUNCHER 1 > tmp/probe/device/launch.txt 2>&1
  sleep 25
  adb shell screencap -p /sdcard/game-before-consent.png
  adb pull /sdcard/game-before-consent.png tmp/probe/device/game-before-consent.png > /dev/null 2>&1
  adb shell uiautomator dump /sdcard/ui-before-consent.xml > tmp/probe/device/ui-dump-before.txt 2>&1
  adb pull /sdcard/ui-before-consent.xml tmp/probe/device/ui-before-consent.xml > /dev/null 2>&1

  # Accept the game's first-run privacy prompt on the disposable emulator only.
  # Emulator screenshot is 1080x1920; the orange Agree button is centered near (780,1280).
  adb shell input tap 780 1280
  sleep 75
  adb shell screencap -p /sdcard/game-after-consent.png
  adb pull /sdcard/game-after-consent.png tmp/probe/device/game-after-consent.png > /dev/null 2>&1
  adb shell uiautomator dump /sdcard/ui-after-consent.xml > tmp/probe/device/ui-dump-after.txt 2>&1
  adb pull /sdcard/ui-after-consent.xml tmp/probe/device/ui-after-consent.xml > /dev/null 2>&1

  adb shell dumpsys activity activities > tmp/probe/device/activities.txt 2>&1
  adb shell dumpsys window windows > tmp/probe/device/windows.txt 2>&1
  adb shell dumpsys connectivity > tmp/probe/device/connectivity.txt 2>&1
  adb shell dumpsys netstats detail > tmp/probe/device/netstats.txt 2>&1
  adb shell screencap -p /sdcard/game-screen.png
  adb pull /sdcard/game-screen.png tmp/probe/device/game-screen.png > /dev/null 2>&1
  adb logcat -d -v threadtime > tmp/probe/device/logcat.txt
  adb shell ls -laR /sdcard/Android/data/com.ruirui.cjjlq > tmp/probe/device/external-data-list.txt 2>&1

  # Test whether this emulator image allows root access for WebView/cache export.
  adb root > tmp/probe/device/adb-root.txt 2>&1
  adb wait-for-device
  sleep 3
  adb pull /data/user/0/com.ruirui.cjjlq tmp/probe/device/private-data-user 2> tmp/probe/device/private-data-user-pull.txt
  adb pull /data/data/com.ruirui.cjjlq tmp/probe/device/private-data-legacy 2> tmp/probe/device/private-data-legacy-pull.txt
  adb pull /sdcard/Android/data/com.ruirui.cjjlq tmp/probe/device/external-data 2> tmp/probe/device/external-data-pull.txt

  adb shell pidof com.ruirui.cjjlq > tmp/probe/device/app-pid.txt 2>&1
  adb shell dumpsys activity top > tmp/probe/device/activity-top.txt 2>&1

  # If WebView remote debugging is enabled, preserve its target list.
  adb forward tcp:9222 localabstract:webview_devtools_remote > tmp/probe/device/devtools-forward.txt 2>&1
  curl -fsS --max-time 5 http://127.0.0.1:9222/json > tmp/probe/device/webview-targets.json 2> tmp/probe/device/webview-targets.err
else
  adb logcat -d -v threadtime > tmp/probe/device/logcat-install-failed.txt
fi

exit 0
