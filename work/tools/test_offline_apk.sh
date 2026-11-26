#!/usr/bin/env bash
set +e
mkdir -p tmp/offline-test
timeout 45s adb wait-for-device > tmp/offline-test/wait-device.txt 2>&1
timeout 30s adb uninstall com.ruirui.cjjlq > tmp/offline-test/uninstall.txt 2>&1
timeout 90s adb install -r dist/super-spirit-ball-offline.apk > tmp/offline-test/install.txt 2>&1
RC=$?
echo "$RC" > tmp/offline-test/install.exitcode
if [ "$RC" -ne 0 ]; then
  timeout 20s adb logcat -d -v threadtime > tmp/offline-test/logcat-install-failed.txt
  exit 1
fi
# Disable emulator networking before the app is opened.
timeout 15s adb shell svc wifi disable > tmp/offline-test/disable-wifi.txt 2>&1
timeout 15s adb shell svc data disable > tmp/offline-test/disable-data.txt 2>&1
timeout 15s adb shell settings put global airplane_mode_on 1
timeout 15s adb shell am broadcast -a android.intent.action.AIRPLANE_MODE --ez state true > tmp/offline-test/airplane.txt 2>&1
timeout 30s adb shell monkey -p com.ruirui.cjjlq -c android.intent.category.LAUNCHER 1 > tmp/offline-test/launch.txt 2>&1
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
# Exercise the restored local daily, weekly and main-story task flows.
# The task shortcut opens the original game task panels backed by local task data.
timeout 10s adb shell input tap 1000 50 > tmp/offline-test/task-shortcut-tap.txt 2>&1
sleep 12
timeout 20s adb shell screencap -p /sdcard/offline-task-daily.png
timeout 30s adb pull /sdcard/offline-task-daily.png tmp/offline-test/offline-task-daily.png > /dev/null 2>&1
# The first ready daily row is login; after that, the pet-upgrade task is ready.
timeout 10s adb shell input tap 891 829 > tmp/offline-test/task-daily-login-claim.txt 2>&1
sleep 4
timeout 10s adb shell input tap 891 829 > tmp/offline-test/task-daily-pet-claim.txt 2>&1
sleep 4
# Claim the first daily activity chest. The first two ready tasks add 20 liveness;
# the archived client may include previously accumulated liveness in the reported total.
timeout 10s adb shell input tap 365 609 > tmp/offline-test/task-daily-box-claim.txt 2>&1
sleep 4
timeout 20s adb shell screencap -p /sdcard/offline-daily-reward-popup.png
timeout 30s adb pull /sdcard/offline-daily-reward-popup.png tmp/offline-test/offline-daily-reward-popup.png > /dev/null 2>&1
# The original Receive panel is modal: confirm before using any other Task controls.
timeout 10s adb shell input tap 540 1354 > tmp/offline-test/daily-reward-confirm.txt 2>&1
sleep 3
timeout 20s adb shell screencap -p /sdcard/offline-task-daily-claimed.png
timeout 30s adb pull /sdcard/offline-task-daily-claimed.png tmp/offline-test/offline-task-daily-claimed.png > /dev/null 2>&1
# Switch to weekly tab, claim its completed local-login task, then main-story tab.
timeout 10s adb shell input tap 350 105 > tmp/offline-test/task-week-tab.txt 2>&1
sleep 5
timeout 20s adb shell screencap -p /sdcard/offline-task-weekly.png
timeout 30s adb pull /sdcard/offline-task-weekly.png tmp/offline-test/offline-task-weekly.png > /dev/null 2>&1
timeout 10s adb shell input tap 891 829 > tmp/offline-test/task-week-login-claim.txt 2>&1
sleep 4
timeout 20s adb shell screencap -p /sdcard/offline-weekly-reward-popup.png
timeout 30s adb pull /sdcard/offline-weekly-reward-popup.png tmp/offline-test/offline-weekly-reward-popup.png > /dev/null 2>&1
# Close the weekly login reward before switching to main-story tasks.
timeout 10s adb shell input tap 540 1354 > tmp/offline-test/weekly-reward-confirm.txt 2>&1
sleep 3
timeout 20s adb shell screencap -p /sdcard/offline-task-weekly-claimed.png
timeout 30s adb pull /sdcard/offline-task-weekly-claimed.png tmp/offline-test/offline-task-weekly-claimed.png > /dev/null 2>&1
# Capture main-story task progress before the first three stages are cleared.
# It is not claimable yet; the claim is exercised after stage 1-6 completes below.
if timeout 15s adb logcat -d -v brief | grep -q "local task panel tabs 4"; then
  timeout 10s adb shell input tap 740 105 > tmp/offline-test/task-main-tab.txt 2>&1
else
  timeout 10s adb shell input tap 480 105 > tmp/offline-test/task-main-tab.txt 2>&1
fi
sleep 5
timeout 20s adb shell screencap -p /sdcard/offline-task-main.png
timeout 30s adb pull /sdcard/offline-task-main.png tmp/offline-test/offline-task-main.png > /dev/null 2>&1
# Close Task before opening Main Challenge so the challenge click is not blocked underneath.
timeout 10s adb shell input tap 1070 1818 > tmp/offline-test/task-panel-close.txt 2>&1
sleep 6
timeout 20s adb shell screencap -p /sdcard/offline-after-task-close.png
timeout 30s adb pull /sdcard/offline-after-task-close.png tmp/offline-test/offline-after-task-close.png > /dev/null 2>&1
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
# Complete three real main-challenge fights so all three starter gear pieces drop.
# Stage 2 follows the first fight. The client opens a result view and auto-continues
# after about 30 seconds; close each result before that transition and observe the next response.
SEEN_STAGE2=0
for attempt in $(seq 1 120); do
  if timeout 15s adb logcat -d -v brief | grep -q "local NewSceneGradeFightRsp 1 -> 2"; then
    SEEN_STAGE2=1
    break
  fi
  sleep 1
done
if [ "$SEEN_STAGE2" -eq 1 ]; then
  sleep 26
  timeout 10s adb shell input tap 800 1675 > tmp/offline-test/stage2-next-stage.txt 2>&1
else
  echo "stage-two reward did not appear" > tmp/offline-test/stage2-next-stage.txt
fi
SEEN_STAGE3=0
for attempt in $(seq 1 45); do
  if timeout 15s adb logcat -d -v brief | grep -q "local NewSceneGradeFightRsp 2 -> 3"; then
    SEEN_STAGE3=1
    break
  fi
  sleep 1
done
if [ "$SEEN_STAGE3" -eq 1 ]; then
  sleep 26
  timeout 10s adb shell input tap 800 1675 > tmp/offline-test/stage3-next-stage.txt 2>&1
else
  echo "stage-three reward did not appear" > tmp/offline-test/stage3-next-stage.txt
fi
SEEN_STAGE4=0
for attempt in $(seq 1 45); do
  if timeout 15s adb logcat -d -v brief | grep -q "local NewSceneGradeFightRsp 3 -> 4"; then
    SEEN_STAGE4=1
    break
  fi
  sleep 1
done
if [ "$SEEN_STAGE4" -eq 1 ]; then
  timeout 20s adb shell screencap -p /sdcard/offline-progress-screen.png
  timeout 30s adb pull /sdcard/offline-progress-screen.png tmp/offline-test/offline-progress-screen.png > /dev/null 2>&1
else
  echo "stage-four reward did not appear" > tmp/offline-test/stage4-result.txt
fi
# The 4 -> 5 response starts stage 1-5; the 5 -> 6 response means
# stage 1-5 has finished and its victory panel is now visible.
SEEN_STAGE5_RESULT=0
if [ "$SEEN_STAGE4" -eq 1 ]; then
  for attempt in $(seq 1 45); do
    if timeout 15s adb logcat -d -v brief | grep -q "local NewSceneGradeFightRsp 5 -> 6"; then
      SEEN_STAGE5_RESULT=1
      break
    fi
    sleep 1
  done
fi
if [ "$SEEN_STAGE5_RESULT" -eq 1 ]; then
  # Wait for the final stage's victory panel, then close it before the next-stage timer fires.
  MAIN_CHALLENGE_RESULT_READY=0
  for attempt in $(seq 1 60); do
    if timeout 15s adb logcat -d -v brief | grep -q "local main challenge result panel ready 6"; then
      MAIN_CHALLENGE_RESULT_READY=1
      break
    fi
    sleep 1
  done
  if [ "$MAIN_CHALLENGE_RESULT_READY" -eq 1 ]; then
    # The dedicated Return to Adventure control stays at a fixed screen position,
    # independent of how many offline self-test buttons are present in the menu.
    timeout 10s adb shell input tap 80 120 > tmp/offline-test/exit-main-challenge.txt 2>&1
    sleep 5
    timeout 20s adb shell screencap -p /sdcard/offline-main-after-challenge.png
    timeout 30s adb pull /sdcard/offline-main-after-challenge.png tmp/offline-test/offline-main-after-challenge.png > /dev/null 2>&1
  else
    echo "stage 1-6 victory result panel did not appear; challenge return not attempted" > tmp/offline-test/exit-main-challenge.txt
  fi
else
  echo "stage 1-6 did not start; challenge return not attempted" > tmp/offline-test/exit-main-challenge.txt
fi
# Claim the main-story task after the stage 1-6 challenge has completed.
timeout 10s adb shell input tap 1000 50 > tmp/offline-test/reopen-task-for-main-claim.txt 2>&1
sleep 8
if timeout 15s adb logcat -d -v brief | grep -q "local task panel tabs 4"; then
  timeout 10s adb shell input tap 740 105 > tmp/offline-test/task-main-tab-after-challenge.txt 2>&1
else
  timeout 10s adb shell input tap 480 105 > tmp/offline-test/task-main-tab-after-challenge.txt 2>&1
fi
sleep 5
timeout 20s adb shell screencap -p /sdcard/offline-task-main.png
timeout 30s adb pull /sdcard/offline-task-main.png tmp/offline-test/offline-task-main.png > /dev/null 2>&1
# Task/MainLine layout: list x=33,y=485; btnGet center x=561,y=68.
# Physical emulator coordinates are scaled by 1.5: (891,829).
timeout 10s adb shell input tap 891 829 > tmp/offline-test/task-main-claim.txt 2>&1
sleep 5
timeout 20s adb shell screencap -p /sdcard/offline-task-main-claimed.png
timeout 30s adb pull /sdcard/offline-task-main-claimed.png tmp/offline-test/offline-task-main-claimed.png > /dev/null 2>&1
timeout 10s adb shell input tap 540 1354 > tmp/offline-test/main-task-reward-confirm.txt 2>&1
sleep 3
# Close Tasks before opening the Spirit page and its equipment slots.
timeout 10s adb shell input tap 1070 1818 > tmp/offline-test/task-panel-close-after-main-claim.txt 2>&1
sleep 4
# The pet tab is on the normal bottom navigation, only after leaving combat.
timeout 10s adb shell input tap 385 1825 > tmp/offline-test/pet-tab-before-equip.txt 2>&1
sleep 7
timeout 20s adb shell screencap -p /sdcard/offline-pet-before-equip.png
timeout 30s adb pull /sdcard/offline-pet-before-equip.png tmp/offline-test/offline-pet-before-equip.png > /dev/null 2>&1
# PokemonMain UI layout places the one-key-wear button at logical (617,717),
# and itemIcon2 at (144,693) with a 120x120 CommonItem hitbox.
# The emulator display is 1.5x the 720x1280 layout coordinates.
timeout 10s adb shell input tap 920 1075 > tmp/offline-test/pet-one-key-equip.txt 2>&1
sleep 8
timeout 20s adb shell screencap -p /sdcard/offline-equipped-screen.png
timeout 30s adb pull /sdcard/offline-equipped-screen.png tmp/offline-test/offline-equipped-screen.png > /dev/null 2>&1
# Slot 1 is empty; the first rewarded gear is in slot 2 (itemIcon2).
# Open that occupied slot to exercise the worn-list and equipment-detail queries.
timeout 10s adb shell input tap 306 1130 > tmp/offline-test/equipment-detail-open.txt 2>&1
sleep 8
timeout 20s adb shell screencap -p /sdcard/offline-equipment-detail-screen.png
timeout 30s adb pull /sdcard/offline-equipment-detail-screen.png tmp/offline-test/offline-equipment-detail-screen.png > /dev/null 2>&1
timeout 10s adb shell input keyevent 4 > tmp/offline-test/equipment-detail-close.txt 2>&1
sleep 5
timeout 20s adb shell uiautomator dump /sdcard/offline-ui.xml > tmp/offline-test/ui-dump.txt 2>&1
timeout 20s adb pull /sdcard/offline-ui.xml tmp/offline-test/ui.xml > /dev/null 2>&1
timeout 20s adb shell dumpsys activity activities > tmp/offline-test/activities.txt 2>&1
timeout 20s adb shell dumpsys window windows > tmp/offline-test/windows.txt 2>&1
timeout 20s adb shell pidof com.ruirui.cjjlq > tmp/offline-test/app-pid.txt 2>&1
# Preserve first-session evidence, then cold-restart while networking remains disabled.
timeout 30s adb logcat -d -v threadtime > tmp/offline-test/first-run-logcat.txt
timeout 10s adb shell am force-stop com.ruirui.cjjlq
sleep 3
timeout 30s adb shell monkey -p com.ruirui.cjjlq -c android.intent.category.LAUNCHER 1 > tmp/offline-test/reload-launch.txt 2>&1
sleep 35
timeout 20s adb shell screencap -p /sdcard/offline-reload-screen.png
timeout 30s adb pull /sdcard/offline-reload-screen.png tmp/offline-test/offline-reload-screen.png > /dev/null 2>&1
timeout 10s adb shell input tap 80 50 > tmp/offline-test/offline-menu-open.txt 2>&1
sleep 2
timeout 20s adb shell screencap -p /sdcard/offline-tools-menu.png
timeout 30s adb pull /sdcard/offline-tools-menu.png tmp/offline-test/offline-tools-menu.png > /dev/null 2>&1
timeout 10s adb shell input tap 150 517 > tmp/offline-test/offline-item-self-test.txt 2>&1
sleep 5
timeout 10s adb shell input tap 150 630 > tmp/offline-test/offline-crystal-self-test.txt 2>&1
sleep 5
timeout 10s adb shell input tap 150 743 > tmp/offline-test/offline-star-self-test.txt 2>&1
sleep 5
timeout 10s adb shell input tap 150 856 > tmp/offline-test/offline-star-card-self-test.txt 2>&1
sleep 5
timeout 10s adb shell input tap 150 969 > tmp/offline-test/offline-evolution-self-test.txt 2>&1
sleep 5
timeout 10s adb shell input tap 150 1082 > tmp/offline-test/offline-hangup-self-test.txt 2>&1
sleep 5
timeout 10s adb shell input tap 150 1195 > tmp/offline-test/offline-quick-hangup-self-test.txt 2>&1
sleep 5
timeout 10s adb shell input tap 150 1308 > tmp/offline-test/offline-seven-day-sign-self-test.txt 2>&1
sleep 5
timeout 20s adb shell screencap -p /sdcard/offline-seven-day-sign.png
timeout 30s adb pull /sdcard/offline-seven-day-sign.png tmp/offline-test/offline-seven-day-sign.png > /dev/null 2>&1
timeout 10s adb shell input tap 150 1421 > tmp/offline-test/offline-nature-power-self-test.txt 2>&1
sleep 5
timeout 20s adb shell screencap -p /sdcard/offline-nature-power.png
timeout 30s adb pull /sdcard/offline-nature-power.png tmp/offline-test/offline-nature-power.png > /dev/null 2>&1
timeout 10s adb shell input tap 150 1534 > tmp/offline-test/offline-life-tree-self-test.txt 2>&1
sleep 8
timeout 10s adb shell input tap 150 1647 > tmp/offline-test/offline-trial-tower-self-test.txt 2>&1
sleep 8
timeout 10s adb shell input tap 80 50 > tmp/offline-test/offline-trial-tower-overlay-close.txt 2>&1
sleep 3
timeout 20s adb shell screencap -p /sdcard/offline-trial-tower.png
timeout 30s adb pull /sdcard/offline-trial-tower.png tmp/offline-test/offline-trial-tower.png > /dev/null 2>&1
timeout 20s adb shell screencap -p /sdcard/offline-life-tree.png
timeout 30s adb pull /sdcard/offline-life-tree.png tmp/offline-test/offline-life-tree.png > /dev/null 2>&1
# Cold-restart again to prove the item and crystal changes themselves survive.
timeout 10s adb shell am force-stop com.ruirui.cjjlq
sleep 3
timeout 30s adb shell monkey -p com.ruirui.cjjlq -c android.intent.category.LAUNCHER 1 > tmp/offline-test/final-reload-launch.txt 2>&1
sleep 30
timeout 20s adb shell screencap -p /sdcard/offline-final-reload-screen.png
timeout 30s adb pull /sdcard/offline-final-reload-screen.png tmp/offline-test/offline-final-reload-screen.png > /dev/null 2>&1
# The offline debug menu is closed after cold restart. Open Town and then tap
# the Life Tree building (the original TownUI btnTree / Doctor Lab).
timeout 10s adb shell input tap 1000 1825 > tmp/offline-test/life-tree-town-open.txt 2>&1
sleep 8
timeout 20s adb shell screencap -p /sdcard/offline-town-screen.png
timeout 30s adb pull /sdcard/offline-town-screen.png tmp/offline-test/offline-town-screen.png > /dev/null 2>&1
timeout 10s adb shell input tap 190 1350 > tmp/offline-test/life-tree-real-open.txt 2>&1
sleep 10
timeout 20s adb shell screencap -p /sdcard/offline-life-tree-real-screen.png
timeout 30s adb pull /sdcard/offline-life-tree-real-screen.png tmp/offline-test/offline-life-tree-real-screen.png > /dev/null 2>&1
timeout 10s adb shell input tap 240 650 > tmp/offline-test/life-tree-real-role-tab.txt 2>&1
sleep 3
timeout 20s adb shell screencap -p /sdcard/offline-life-tree-role-screen.png
timeout 30s adb pull /sdcard/offline-life-tree-role-screen.png tmp/offline-test/offline-life-tree-role-screen.png > /dev/null 2>&1
timeout 30s adb logcat -d -v threadtime > tmp/offline-test/final-reload-logcat.txt
cat tmp/offline-test/first-run-logcat.txt tmp/offline-test/reload-logcat.txt tmp/offline-test/final-reload-logcat.txt > tmp/offline-test/logcat.txt
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
  && grep -q "local task box claimed daily 1 liveness " tmp/offline-test/logcat.txt \
  && grep -q "local task claimed weekly 3 liveness 10" tmp/offline-test/logcat.txt \
  && grep -q "local main task claimed 1 next 2" tmp/offline-test/logcat.txt \
  && grep -q "local equipment item reward 4000002 1 position 2" tmp/offline-test/logcat.txt \
  && grep -q "local equipment item reward 4000003 1 position 3" tmp/offline-test/logcat.txt \
  && grep -q "local equipment item reward 4000004 1 position 4" tmp/offline-test/logcat.txt \
  && grep -q "local equipment auto-wear 1 equipped 3 positions 2,3,4" tmp/offline-test/logcat.txt \
  && grep -q "local equipment auto-wear 1 equipped 3 positions 2,3,4 bonus 3125 229 175" tmp/offline-test/logcat.txt \
  && grep -q "local equipment inventory query 2 1" tmp/offline-test/logcat.txt \
  && grep -q "local equipment inventory detail 2 1 3101 hp 3125" tmp/offline-test/logcat.txt \
  && grep -q "local save restored equipment 4 12" tmp/offline-test/logcat.txt \
  && grep -q "local item operations self-test PASS" tmp/offline-test/logcat.txt \
  && grep -q "local pet crystal self-test PASS" tmp/offline-test/logcat.txt \
  && grep -q "local pet star-up self-test PASS" tmp/offline-test/logcat.txt \
  && grep -q "local pet star-card self-test PASS" tmp/offline-test/logcat.txt \
  && grep -q "local pet evolution self-test PASS" tmp/offline-test/logcat.txt \
  && grep -q "local hangup self-test PASS query 0 claim 0 duplicate 1 under60 PASS" tmp/offline-test/logcat.txt \
  && grep -q "local quick hangup self-test PASS query 0 claim 0 duplicate 1 paid 1 rewards 12" tmp/offline-test/logcat.txt \
  && grep -q "local seven day sign self-test PASS day 1 duplicate 1 dayReset PASS rewards 1" tmp/offline-test/logcat.txt \
  && grep -q "local save restored seven day sign 1 1" tmp/offline-test/logcat.txt \
  && grep -q "local nature power self-test PASS query 0 upgrade 0 duplicate 1 resource PASS" tmp/offline-test/logcat.txt \
  && grep -q "local save restored nature power 1" tmp/offline-test/logcat.txt \
  && grep -q "local life tree self-test PASS overview PASS base 10 roles 10,10,10,10,10 stale 1 cap 1 attrs PASS passives 100 4 1 trainerLevel 50" tmp/offline-test/logcat.txt \
  && grep -q "local save restored life tree 10 10 10 10 10 10" tmp/offline-test/logcat.txt \
  && grep -q "local LifeTreeOperate overview 6 10" tmp/offline-test/logcat.txt \
  && grep -q "local trial tower self-test PASS overview PASS battle PASS sparse PASS schedule PASS stale 1 skip 0 award 0 duplicate 1 history 1 level 241 dayCount 2 milestone 100048" tmp/offline-test/logcat.txt \
  && grep -q "local save restored trial tower 241 2 100048 100001" tmp/offline-test/logcat.txt \
  && grep -q "local TrialTower actual entry opened" tmp/offline-test/logcat.txt \
  && grep -q "local save restored star-up pet 3" tmp/offline-test/logcat.txt \
  && grep -q "local save restored star-up batch 2" tmp/offline-test/logcat.txt \
  && grep -q "local save restored card-star-up pet 6" tmp/offline-test/logcat.txt \
  && grep -q "local save restored pet evolution 1208" tmp/offline-test/logcat.txt \
  && grep -q "local save restored pet evolution gear 3125" tmp/offline-test/logcat.txt \
  && grep -q "local main challenge result panel ready 6" tmp/offline-test/logcat.txt \
  && grep -q "local main challenge sequence complete 6" tmp/offline-test/logcat.txt \
  && grep -q "local return to adventure closed CombatWinUI1" tmp/offline-test/logcat.txt \
  && grep -q "local return to adventure closed MainChallenge" tmp/offline-test/logcat.txt \
  && ! grep -q "local NewSceneGradeFightRsp 6 -> 7" tmp/offline-test/logcat.txt \
  && ! grep -q "local inventory listener 2 TypeError" tmp/offline-test/logcat.txt \
  && grep -q "local save restored pet crystal 0 2 1 0" tmp/offline-test/logcat.txt \
  && grep -Eq "local save restored hangup [1-9][0-9]* 0 PRESERVED" tmp/offline-test/logcat.txt \
  && grep -q "local save restored quick hangup 0 saved 1 dayReset 1" tmp/offline-test/logcat.txt \
  && grep -q "local save restored item operations 1 1" tmp/offline-test/logcat.txt \
  && grep -q "local pet equipment bonus 1 hp 3125 attack 229 defense 175 lifeTree 0 0 combat 17425 2649 1495" tmp/offline-test/logcat.txt \
   && test -s tmp/offline-test/offline-pet-main-screen.png \
  && test -s tmp/offline-test/offline-main-after-challenge.png \
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
  && grep -q "local equipment item reward 4000004 1 position 4" tmp/offline-test/logcat.txt \
  && grep -q "local NewSceneGradeFightRsp 1 -> 2" tmp/offline-test/logcat.txt \
  && grep -q "local gold reward" tmp/offline-test/logcat.txt \
  && grep -q "local save restored 1109500 6" tmp/offline-test/logcat.txt \
  && [ -z "$FATAL_JS" ] \
  && ! grep -q "Failed to load: atlas/NewBag.atlas" tmp/offline-test/logcat.txt \
  && ! grep -q "Failed to load: atlas/receive" tmp/offline-test/logcat.txt \
  && ! grep -q "Failed to load: atlas/receive/huode_shilianb.png" tmp/offline-test/logcat.txt \
  && ! grep -q "Failed to load: atlas/equipmentAlert.atlas" tmp/offline-test/logcat.txt \
  && ! grep -q "Failed to load: atlas/ElfSummon.atlas" tmp/offline-test/logcat.txt \
  && ! grep -q "Failed to load: atlas/Town.atlas" tmp/offline-test/logcat.txt \
  && ! grep -q "Failed to load: atlas/LifeTree.atlas" tmp/offline-test/logcat.txt \
  && ! grep -q "Failed to load: atlas/TrialTower.atlas" tmp/offline-test/logcat.txt \
  && ! grep -q "GroupLoader.*TrialTower.*Load Error" tmp/offline-test/logcat.txt \
  && ! grep -q "GroupLoader.*LifeTree.*Load Error" tmp/offline-test/logcat.txt \
  && ! grep -Fq '"[Offline] unhandledrejection' tmp/offline-test/logcat.txt \
  && ! grep -q "Failed to load: atlas/PerserateSpace/Ani3.atlas" tmp/offline-test/logcat.txt \
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
  && test -s tmp/offline-test/offline-tools-menu.png \
  && test -s tmp/offline-test/offline-final-reload-screen.png \
  && test -s tmp/offline-test/offline-seven-day-sign.png \
  && test -s tmp/offline-test/offline-nature-power.png \
  && test -s tmp/offline-test/offline-life-tree.png \
  && test -s tmp/offline-test/offline-trial-tower.png \
  && test -s tmp/offline-test/offline-town-screen.png \
  && test -s tmp/offline-test/offline-life-tree-real-screen.png \
  && test -s tmp/offline-test/offline-life-tree-role-screen.png \
  && test -s tmp/offline-test/offline-task-daily.png \
  && test -s tmp/offline-test/offline-task-daily-claimed.png \
  && test -s tmp/offline-test/offline-task-weekly.png \
  && test -s tmp/offline-test/offline-weekly-reward-popup.png \
  && test -s tmp/offline-test/offline-task-weekly-claimed.png \
  && test -s tmp/offline-test/offline-task-main.png \
  && test -s tmp/offline-test/offline-task-main-claimed.png \
  && test -s tmp/offline-test/offline-daily-reward-popup.png \
  && test -s tmp/offline-test/offline-equipped-screen.png \
  && test -s tmp/offline-test/offline-equipment-detail-screen.png \
  && test -s tmp/offline-test/offline-after-task-close.png; then
  echo "OFFLINE_SCENE_TEST=PASS" | tee -a tmp/offline-test/SUMMARY.txt
  exit 0
fi
echo "OFFLINE_SCENE_TEST=FAIL (scene/login/main PvE response, rewards, save restore, combat animation atlas, fatal JS rejection, missing assets, or native network dialog)" | tee -a tmp/offline-test/SUMMARY.txt
exit 1
