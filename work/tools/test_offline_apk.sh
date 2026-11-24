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
sleep 100
timeout 20s adb shell screencap -p /sdcard/offline-game-screen.png
timeout 30s adb pull /sdcard/offline-game-screen.png tmp/offline-test/offline-game-screen.png > /dev/null 2>&1
# Tap the map to verify that the local trainer can move.
timeout 10s adb shell input tap 650 790 > tmp/offline-test/map-tap.txt 2>&1
sleep 5
timeout 20s adb shell screencap -p /sdcard/offline-move-screen.png
timeout 30s adb pull /sdcard/offline-move-screen.png tmp/offline-test/offline-move-screen.png > /dev/null 2>&1
# The Quick Battle shortcut is in the upper-right row above the bottom tabs.
# The 720x1280 game canvas is scaled to the 1080x1920 emulator display.
timeout 10s adb shell input tap 1010 1640 > tmp/offline-test/quick-battle-tap.txt 2>&1
sleep 5
timeout 20s adb shell screencap -p /sdcard/offline-quick-combat-panel.png
timeout 30s adb pull /sdcard/offline-quick-combat-panel.png tmp/offline-test/offline-quick-combat-panel.png > /dev/null 2>&1
# Quick Combat panel's yellow claim button is centered at logical (336,806).
timeout 10s adb shell input tap 504 1209 > tmp/offline-test/claim-quick-battle-tap.txt 2>&1
sleep 20
timeout 20s adb shell screencap -p /sdcard/offline-battle-screen.png
timeout 30s adb pull /sdcard/offline-battle-screen.png tmp/offline-test/offline-battle-screen.png > /dev/null 2>&1
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
  grep -iE "\\[Offline\\]|offline patch|local LoginRsp|EnterSceneRsp|file:///android_asset/game|ERR_FILE_NOT_FOUND|FATAL EXCEPTION|Uncaught" tmp/offline-test/logcat.txt | tail -n 800 || true
  echo "=== dynamic battle resource errors ==="
  grep -iE "Failed to load: res/combat|Unable to open asset URL: file:///android_asset/game/res/combat" tmp/offline-test/logcat.txt | tail -n 250 || true
  echo "=== network errors ==="
  grep -iE "ERR_INTERNET_DISCONNECTED|ERR_NAME_NOT_RESOLVED|UnknownHost|网络不可用" tmp/offline-test/logcat.txt | tail -n 200 || true
} > tmp/offline-test/SUMMARY.txt
cat tmp/offline-test/SUMMARY.txt
BAD_JS='Uncaught( \(in promise\))? (TypeError|ReferenceError|NotSupportedError)|\\[Offline\\] unhandledrejection (TypeError|ReferenceError|NotSupportedError)'
# Ignore only the single native callback race emitted before the page is parsed.
FATAL_JS=$(grep -E "$BAD_JS" tmp/offline-test/logcat.txt | grep -vF "Uncaught ReferenceError: CallbackFromAndroid is not defined" || true)
if grep -q "local LoginRsp" tmp/offline-test/logcat.txt \
  && grep -q "local EnterSceneRsp + labelled bots" tmp/offline-test/logcat.txt \
  && [ "$(grep -c "local QuickHangupOperateRsp" tmp/offline-test/logcat.txt)" -ge 2 ] \
  && grep -q "local gold reward" tmp/offline-test/logcat.txt \
  && [ -z "$FATAL_JS" ] \
  && ! grep -q "Failed to load: atlas/role/1.atlas" tmp/offline-test/logcat.txt \
  && ! grep -q "Failed to load: role/1/" tmp/offline-test/logcat.txt \
  && ! grep -q "Failed to load: res/combat/skills/" tmp/offline-test/logcat.txt \
  && ! grep -q "Failed to load: res/combat/spirits/" tmp/offline-test/logcat.txt \
  && ! grep -q "网络不可用，请检查网络状态" tmp/offline-test/ui.xml \
  && test -s tmp/offline-test/offline-game-screen.png \
  && test -s tmp/offline-test/offline-move-screen.png \
  && test -s tmp/offline-test/offline-quick-combat-panel.png \
  && test -s tmp/offline-test/offline-battle-screen.png; then
  echo "OFFLINE_SCENE_TEST=PASS" | tee -a tmp/offline-test/SUMMARY.txt
  exit 0
fi
echo "OFFLINE_SCENE_TEST=FAIL (scene/login/quick battle response missing, fatal JS rejection, missing role/combat assets, or native network dialog)" | tee -a tmp/offline-test/SUMMARY.txt
exit 1
