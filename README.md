# 超级精灵球离线版

<badge>断网模拟器验收通过</badge>

核心单机流程已经通过 Android 30（x86_64）模拟器的断网端到端回归。最新通过记录为 [GitHub Actions #162](https://github.com/chenmoulaile/apk/actions/runs/45595325360)，日志包含 `OFFLINE_SCENE_TEST=PASS`。

## 已通过的功能

测试在安装 APK 后关闭 Wi-Fi、移动数据并开启飞行模式，再启动游戏。第 157 次完整回归确认：

- 从 APK 内置的本地 H5 页面启动并完成离线登录，进入主城；角色可以移动。
- 主线第 2 至第 6 关可以连续战斗、显示胜利结算、发放奖励并推进关卡。
- 主线任务可以领取；装备自动穿戴、装备库存详情和装备属性加成都能正常显示。
- 道具出售、使用、合成和分解自检通过；宠物水晶解锁、放置、取下和清除冷却自检通过。
- 精灵基础成长、精灵仓库和 18 个编队槽位正常。
- 断网强制结束进程并重新启动后，本地存档能够恢复：金币 1,109,500、第 6 关进度、2 级精灵、普通点数 19,000、活动点数 4,000，以及背包、装备和水晶状态。

测试截图、日志、摘要和 APK 位于 [Actions #162 → Artifacts → offline-apk-test-162](https://github.com/chenmoulaile/apk/actions/runs/45595325360)。

## 下载 APK

从 [Actions #162 的 Artifacts](https://github.com/chenmoulaile/apk/actions/runs/45595325360) 下载 `offline-apk-test-162`，其中包含 `dist/super-spirit-ball-offline.apk`、SHA-256 校验文件和构建说明。

- SHA-256：`6cdcb7becfc359c9a0ac02675edca15c732d2f17fb60df8f8a5aa461e2d4f029`
- 通过环境：Android 30、x86_64 模拟器，断网模式。
- APK 使用本地测试签名，与原版发布者签名不同。
- 从原版切换到此 APK 通常需要先卸载原版；卸载可能清除原版应用数据。

真实设备型号、系统版本和分辨率尚未逐一覆盖，因此模拟器通过不代表所有实体设备均已验证。

## 尚未完整恢复的部分

这不是原版全部线上服务的完整复刻：

- PvE 战斗使用本地确定性战斗模拟器；关卡与敌方配置来自恢复的游戏资源，但伤害、技能和服务端判定并非原服务端算法的完整复刻。
- 排行榜、聊天、真实玩家互动、支付、广告、分享及在线服务没有真实联网功能。
- 宠物升星、魂灵卡升星和进化正在独立功能分支进行断网专项验证，尚未计入第 157 次主分支通过范围。
- 其他活动、副本和深层养成系统仍需逐项实现和实机验证。

因此，目前可以称为**核心流程可断网游玩的单机版本**，还不能称为完整复刻原版全部玩法。

## 构建与实现

- `work/tools/patch_offline_h5.py`：离线登录、本地数据、存档、道具、装备和本地 PvE 逻辑。
- `work/tools/patch_android.py`：将 Android WebView 的入口指向 APK 内置 H5。
- `work/tools/test_offline_apk.sh`：断网启动、任务、战斗、奖励、宠物、装备和冷启动回归。
- `.github/workflows/offline-build.yml`：恢复资源、重打包、签名并运行 Android 模拟器验收。

构建工件只有在断网模拟器测试通过后，才会把构建说明中的验证状态标为 `OFFLINE_SCENE_TEST=PASS`。
