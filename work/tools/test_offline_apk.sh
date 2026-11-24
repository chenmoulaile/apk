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
# Main Challenge button center: logical (355,1078), scaled to 1080x1920.
timeout 10s adb shell input tap 533 1617 > tmp/offline-test/main-challenge-tap.txt 2>&1
sleep 5
timeout 20s adb shell screencap -p /sdcard/offline-main-challenge-panel.png
timeout 30s adb pull /sdcard/offline-main-challenge-panel.png tmp/offline-test/offline-main-challenge-panel.png > /dev/null 2>&1
# Challenge button center: panel origin (12,126) + local (346,893), scaled 1.5x.
timeout 10s adb shell input tap 537 1529 > tmp/offline-test/open-formation-tap.txt 2>&1
sleep 5
timeout 20s adb shell screencap -p /sdcard/offline-combat-formation-panel.png
timeout 30s adb pull /sdcard/offline-combat-formation-panel.png tmp/offline-test/offline-combat-formation-panel.png > /dev/null 2>&1
# Formation Fight button center at logical (453,1218), scaled 1.5x.
timeout 10s adb shell input tap 680 1827 > tmp/offline-test/start-main-fight-tap.txt 2>&1
sleep 25
timeout 20s adb shell screencap -p /sdcard/offline-battle-screen.png
timeout 30s adb pull /sdcard/offline-battle-screen.png tmp/offline-test/offline-battle-screen.png > /dev/null 2>&1
timeout 20s adb shell uiautomator dump /sdcard/offline-ui.xml > tmp/offline-test/ui-dump.txt 2>&1
timeout 20s adb pull /sdcard/offline-ui.xml tmp/offline-test/ui.xml > /dev/null 2>&1
timeout 20s adb shell dumpsys activity activities > tmp/offline-test/activities.txt 2>&1
timeout 20s adb shell dumpsys window windows > tmp/offline-test/windows.txt 2>&1
timeout 20s adb shell pidof com.ruirui.cjjlq > tmp/offline-test/app-pid.txt 2>&1
# Preserve first-session evidence, then cold-restart while networking remains disabled.
timeout 30s adb logcat -d -v threadtime > tmp/offline-test/first-run-logcat.txt
adb shell am force-stop com.ruirui.cjjlq
sleep 3
adb shell monkey -p com.ruirui.cjjlq -c android.intent.category.LAUNCHER 1 > tmp/offline-test/reload-launch.txt 2>&1
sleep 35
timeout 20s adb shell screencap -p /sdcard/offline-reload-screen.png
timeout 30s adb pull /sdcard/offline-reload-screen.png tmp/offline-test/offline-reload-screen.png > /dev/null 2>&1
timeout 30s adb logcat -d -v threadtime > tmp/offline-test/reload-logcat.txt
cat tmp/offline-test/first-run-logcat.txt tmp/offline-test/reload-logcat.txt > tmp/offline-test/logcat.txt
{
  echo "=== install ==="
  cat tmp/offline-test/install.txt
  echo "=== app pid ==="
  cat tmp/offline-test/app-pid.txt
  echo "=== Offline H5 log lines ==="
  grep -iE "\\[Offline\\]|offline patch|local LoginRsp|EnterSceneRsp|local save restored|file:///android_asset/game|ERR_FILE_NOT_FOUND|FATAL EXCEPTION|Uncaught" tmp/offline-test/logcat.txt | tail -n 800 || true
  echo "=== dynamic battle resource errors ==="
  grep -iE "Failed to load: res/combat|Unable to open asset URL: file:///android_asset/game/res/combat" tmp/offline-test/logcat.txt | tail -n 250 || true
  echo "=== network errors ==="
  grep -iE "ERR_INTERNET_DISCONNECTED|ERR_NAME_NOT_RESOLVED|UnknownHost|网络不可用" tmp/offline-test/logcat.txt | tail -n 200 || true
} > tmp/offline-test/SUMMARY.txt
cat tmp/offline-test/SUMMARY.txt
BAD_JS='Uncaught( \(in promise\))? (TypeError|ReferenceError|NotSupportedError)|\\[Offline\\] unhandledrejection (TypeError|ReferenceError|NotSupportedError)'
# Fail on every uncaught JavaScript exception, including early native callback races.
FATAL_JS=$(grep -E "$BAD_JS" tmp/offline-test/logcat.txt || true)
if grep -q "local LoginRsp" tmp/offline-test/logcat.txt \
  && grep -q "local EnterSceneRsp + labelled bots" tmp/offline-test/logcat.txt \
  && grep -q "local NewSceneGradeFightRsp" tmp/offline-test/logcat.txt \
  && grep -q "local gold reward" tmp/offline-test/logcat.txt \
  && grep -q "local save restored 1030000 4" tmp/offline-test/logcat.txt \
  && [ -z "$FATAL_JS" ] \
  && ! grep -q "Failed to load: atlas/role/1.atlas" tmp/offline-test/logcat.txt \
  && ! grep -q "Failed to load: role/1/" tmp/offline-test/logcat.txt \
  && ! grep -q "Failed to load: res/combat/skills/" tmp/offline-test/logcat.txt \
  && ! grep -q "Failed to load: res/combat/spirits/" tmp/offline-test/logcat.txt \
  && ! grep -q "Failed to load: atlas/CombatFormation/" tmp/offline-test/logcat.txt \
  && ! grep -q "Failed to load: atlas/Checkpoint/MainChallenge/" tmp/offline-test/logcat.txt \
  && ! grep -q "Failed to load: atlas/CombatFormation.atlas" tmp/offline-test/logcat.txt \
  && ! grep -q "Failed to load: atlas/Checkpoint/MainChallenge.atlas" tmp/offline-test/logcat.txt \
  && ! grep -q "Failed to load: atlas/Checkpoint/offLineGiftPanel.atlas" tmp/offline-test/logcat.txt \
  && ! grep -q "Failed to load: atlas/combat/result.atlas" tmp/offline-test/logcat.txt \
  && ! grep -q "Failed to load: atlas/combat/animation/" tmp/offline-test/logcat.txt \
  && ! grep -q "Failed to load: res/items/" tmp/offline-test/logcat.txt \
  && ! grep -q "Failed to load: res/icons/" tmp/offline-test/logcat.txt \
  && ! grep -q "unhandledrejection TypeError" tmp/offline-test/logcat.txt \
  && grep -q "local ani1 atlas frames registered 8" tmp/offline-test/logcat.txt \
  && ! grep -q "local ani1 atlas frames unavailable after retry" tmp/offline-test/logcat.txt \
  && ! grep -q "lost skin: combat/ani1/" tmp/offline-test/logcat.txt \
  && ! grep -q "网络不可用，请检查网络状态" tmp/offline-test/ui.xml \
  && test -s tmp/offline-test/offline-game-screen.png \
  && test -s tmp/offline-test/offline-move-screen.png \
  && test -s tmp/offline-test/offline-main-challenge-panel.png \
  && test -s tmp/offline-test/offline-combat-formation-panel.png \
  && test -s tmp/offline-test/offline-battle-screen.png \
  && test -s tmp/offline-test/offline-reload-screen.png; then
  echo "OFFLINE_SCENE_TEST=PASS" | tee -a tmp/offline-test/SUMMARY.txt
  exit 0
fi
echo "OFFLINE_SCENE_TEST=FAIL (scene/login/main PvE response, rewards, save restore, combat animation atlas, fatal JS rejection, missing assets, or native network dialog)" | tee -a tmp/offline-test/SUMMARY.txt
exit 1
