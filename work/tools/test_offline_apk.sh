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
# Open the Spirit page and verify the local pet's base attributes.
timeout 10s adb shell input tap 385 1825 > tmp/offline-test/pet-tab-tap.txt 2>&1
sleep 8
timeout 20s adb shell screencap -p /sdcard/offline-pet-main-screen.png
timeout 30s adb pull /sdcard/offline-pet-main-screen.png tmp/offline-test/offline-pet-main-screen.png > /dev/null 2>&1
# Open Level Up, request one real config-priced growth step, then capture the result.
timeout 10s adb shell input tap 160 1623 > tmp/offline-test/pet-levelup-tap.txt 2>&1
sleep 6
timeout 20s adb shell screencap -p /sdcard/offline-pet-levelup-screen.png
timeout 30s adb pull /sdcard/offline-pet-levelup-screen.png tmp/offline-test/offline-pet-levelup-screen.png > /dev/null 2>&1
timeout 10s adb shell input tap 650 1555 > tmp/offline-test/pet-growup-tap.txt 2>&1
sleep 4
timeout 20s adb shell screencap -p /sdcard/offline-pet-levelup-after.png
timeout 30s adb pull /sdcard/offline-pet-levelup-after.png tmp/offline-test/offline-pet-levelup-after.png > /dev/null 2>&1
# Close the strengthen overlay and open the storage replacement picker.
timeout 10s adb shell input tap 1024 177 > tmp/offline-test/pet-strengthen-close.txt 2>&1
sleep 3
timeout 20s adb shell screencap -p /sdcard/offline-pet-after-growup-close.png
timeout 30s adb pull /sdcard/offline-pet-after-growup-close.png tmp/offline-test/offline-pet-after-growup-close.png > /dev/null 2>&1
sleep 5
timeout 10s adb shell input tap 980 374 > tmp/offline-test/pet-replace-tap.txt 2>&1
sleep 10
timeout 20s adb shell screencap -p /sdcard/offline-pet-storage-screen.png
timeout 30s adb pull /sdcard/offline-pet-storage-screen.png tmp/offline-test/offline-pet-storage-screen.png > /dev/null 2>&1
# Close the modal replacement picker using its visible close button, then return to Adventure.
timeout 10s adb shell input tap 1008 254 > tmp/offline-test/pet-picker-close-tap.txt 2>&1
sleep 5
timeout 20s adb shell screencap -p /sdcard/offline-pet-closed-screen.png
timeout 30s adb pull /sdcard/offline-pet-closed-screen.png tmp/offline-test/offline-pet-closed-screen.png > /dev/null 2>&1
timeout 10s adb shell input tap 535 1835 > tmp/offline-test/adventure-tab-return.txt 2>&1
sleep 5
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
# Main Challenge auto-advances after each win. Allow stages 2 through 6 to finish.
sleep 110
timeout 20s adb shell screencap -p /sdcard/offline-progress-screen.png
timeout 30s adb pull /sdcard/offline-progress-screen.png tmp/offline-test/offline-progress-screen.png > /dev/null 2>&1
timeout 20s adb shell uiautomator dump /sdcard/offline-ui.xml > tmp/offline-test/ui-dump.txt 2>&1
timeout 20s adb pull /sdcard/offline-ui.xml tmp/offline-test/ui.xml > /dev/null 2>&1
timeout 20s adb shell dumpsys activity activities > tmp/offline-test/activities.txt 2>&1
timeout 20s adb shell dumpsys window windows > tmp/offline-test/windows.txt 2>&1
timeout 20s adb shell pidof com.ruirui.cjjlq > tmp/offline-test/app-pid.txt 2>&1
# Exercise the restored local daily, weekly and main-story task flows.
# The task shortcut opens the original game task panels backed by local task data.
timeout 10s adb shell input tap 1030 30 > tmp/offline-test/task-shortcut-tap.txt 2>&1
sleep 12
timeout 20s adb shell screencap -p /sdcard/offline-task-daily.png
timeout 30s adb pull /sdcard/offline-task-daily.png tmp/offline-test/offline-task-daily.png > /dev/null 2>&1
# The first ready daily row is login; after that, the pet-upgrade task is ready.
timeout 10s adb shell input tap 891 829 > tmp/offline-test/task-daily-login-claim.txt 2>&1
sleep 4
timeout 10s adb shell input tap 891 829 > tmp/offline-test/task-daily-pet-claim.txt 2>&1
sleep 4
# First daily activity chest requires 20 liveness.
timeout 10s adb shell input tap 365 609 > tmp/offline-test/task-daily-box-claim.txt 2>&1
sleep 4
timeout 20s adb shell screencap -p /sdcard/offline-task-daily-claimed.png
timeout 30s adb pull /sdcard/offline-task-daily-claimed.png tmp/offline-test/offline-task-daily-claimed.png > /dev/null 2>&1
# Switch to weekly tab, claim its completed local-login task, then main-story tab.
timeout 10s adb shell input tap 350 105 > tmp/offline-test/task-week-tab.txt 2>&1
sleep 5
timeout 20s adb shell screencap -p /sdcard/offline-task-weekly.png
timeout 30s adb pull /sdcard/offline-task-weekly.png tmp/offline-test/offline-task-weekly.png > /dev/null 2>&1
timeout 10s adb shell input tap 891 829 > tmp/offline-test/task-week-login-claim.txt 2>&1
sleep 4
# Main-story tab is the third tab when the optional training tab is locked,
# and the fourth tab when training is available.
if grep -q "local task panel tabs 4" tmp/offline-test/first-run-logcat.txt 2>/dev/null; then
  adb shell input tap 740 105 > tmp/offline-test/task-main-tab.txt 2>&1
else
  adb shell input tap 545 105 > tmp/offline-test/task-main-tab.txt 2>&1
fi
sleep 5
timeout 20s adb shell screencap -p /sdcard/offline-task-main.png
timeout 30s adb pull /sdcard/offline-task-main.png tmp/offline-test/offline-task-main.png > /dev/null 2>&1
timeout 10s adb shell input tap 891 829 > tmp/offline-test/task-main-claim.txt 2>&1
sleep 5
timeout 20s adb shell screencap -p /sdcard/offline-task-main-claimed.png
timeout 30s adb pull /sdcard/offline-task-main-claimed.png tmp/offline-test/offline-task-main-claimed.png > /dev/null 2>&1
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
if grep -q "local pet seed attrs 3101 2200 1200 13000" tmp/offline-test/logcat.txt \
  && grep -q "local pet seed score 3101 48300" tmp/offline-test/logcat.txt \
  && grep -q "local upgrade flash animation skipped: original frames unavailable" tmp/offline-test/logcat.txt \
  && grep -q "local pet growup 0 1->2 hp 14300 attack 2420 defense 1320 score 53130" tmp/offline-test/logcat.txt \
  && grep -q "local scene reward actions 103:4000002,1|103:1001019,10|100:200|101:20000" tmp/offline-test/logcat.txt \
  && grep -q "local point item reward 59 1000 1000" tmp/offline-test/logcat.txt \
  && grep -q "local save restored 1109500 6" tmp/offline-test/logcat.txt \
  && grep -q "local save restored pet 2 14300 2420 1320" tmp/offline-test/logcat.txt \
  && grep -q "local save restored points 19000 4000" tmp/offline-test/logcat.txt \
  && grep -q "local save restored inventory 18" tmp/offline-test/logcat.txt \
  && grep -q "local pet storage loaded 1 18" tmp/offline-test/logcat.txt \
  && grep -q "local NewTaskInfoOperate 0 daily 16 week 15 main 1" tmp/offline-test/logcat.txt \
  && grep -q "local task claimed daily 1 liveness 10" tmp/offline-test/logcat.txt \
  && grep -q "local task claimed daily 13 liveness 10" tmp/offline-test/logcat.txt \
  && grep -q "local task box claimed daily 1 liveness 20" tmp/offline-test/logcat.txt \
  && grep -q "local task claimed weekly 3 liveness 10" tmp/offline-test/logcat.txt \
  && grep -q "local main task claimed 1 next 2" tmp/offline-test/logcat.txt \
   && test -s tmp/offline-test/offline-pet-main-screen.png \
   && test -s tmp/offline-test/offline-pet-after-growup-close.png \
  && test -s tmp/offline-test/offline-pet-storage-screen.png \
  && test -s tmp/offline-test/offline-pet-levelup-screen.png \
  && test -s tmp/offline-test/offline-pet-levelup-after.png \
  && test -s tmp/offline-test/offline-pet-closed-screen.png \
  && grep -q "local LoginRsp" tmp/offline-test/logcat.txt \
  && grep -q "local EnterSceneRsp + labelled bots" tmp/offline-test/logcat.txt \
  && grep -q "local combat simulation stage 2 rounds .*enemies 0/4 result 1" tmp/offline-test/logcat.txt \
  && grep -q "local NewSceneGradeFightRsp 1 -> 2" tmp/offline-test/logcat.txt \
  && grep -q "local NewSceneGradeFightRsp 2 -> 3" tmp/offline-test/logcat.txt \
  && grep -q "local NewSceneGradeFightRsp 3 -> 4" tmp/offline-test/logcat.txt \
  && grep -q "local combat simulation stage 5 rounds .*enemies 0/4 result 1" tmp/offline-test/logcat.txt \
  && grep -q "local NewSceneGradeFightRsp 4 -> 5" tmp/offline-test/logcat.txt \
  && grep -q "local combat simulation stage 6 rounds .*enemies 0/4 result 1" tmp/offline-test/logcat.txt \
  && grep -q "local NewSceneGradeFightRsp 5 -> 6" tmp/offline-test/logcat.txt \
  && grep -q "local gold reward" tmp/offline-test/logcat.txt \
  && grep -q "local save restored 1109500 6" tmp/offline-test/logcat.txt \
  && [ -z "$FATAL_JS" ] \
  && ! grep -q "Failed to load: atlas/NewBag.atlas" tmp/offline-test/logcat.txt \
  && ! grep -q "Failed to load: atlas/ZPower.atlas" tmp/offline-test/logcat.txt \
  && ! grep -q "Failed to load: atlas/upgradeLight.atlas" tmp/offline-test/logcat.txt \
  && grep -q "local optional atlas group skipped ZPower" tmp/offline-test/logcat.txt \
  && grep -q "local optional atlas group skipped upgradeLight" tmp/offline-test/logcat.txt \
  && ! grep -q "Uncaught (in promise) undefined" tmp/offline-test/logcat.txt \
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
  && test -s tmp/offline-test/offline-pet-storage-screen.png \
  && test -s tmp/offline-test/offline-main-challenge-panel.png \
  && test -s tmp/offline-test/offline-combat-formation-panel.png \
  && test -s tmp/offline-test/offline-battle-screen.png \
  && test -s tmp/offline-test/offline-progress-screen.png \
  && test -s tmp/offline-test/offline-reload-screen.png \
  && test -s tmp/offline-test/offline-task-daily.png \
  && test -s tmp/offline-test/offline-task-daily-claimed.png \
  && test -s tmp/offline-test/offline-task-weekly.png \
  && test -s tmp/offline-test/offline-task-main.png \
  && test -s tmp/offline-test/offline-task-main-claimed.png; then
  echo "OFFLINE_SCENE_TEST=PASS" | tee -a tmp/offline-test/SUMMARY.txt
  exit 0
fi
echo "OFFLINE_SCENE_TEST=FAIL (scene/login/main PvE response, rewards, save restore, combat animation atlas, fatal JS rejection, missing assets, or native network dialog)" | tee -a tmp/offline-test/SUMMARY.txt
exit 1
