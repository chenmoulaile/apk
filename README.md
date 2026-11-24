# 超级精灵球离线化

> 当前状态：**核心单机流程已通过断网 Android 模拟器验收，最新通过版本为 [Actions #110](https://github.com/chenmoulaile/apk/actions/runs/45419753231)。** 日志包含 `OFFLINE_SCENE_TEST=PASS`。

## 已通过的断网功能

在 Android 30（x86_64）模拟器中，安装 APK 后先关闭 Wi-Fi、移动数据并开启飞行模式，再启动游戏。最新端到端测试确认：

- 从 APK 内置的本地 H5 入口启动：`file:///android_asset/game/index.html`。
- 离线登录并进入主城，角色移动正常。
- 精灵成长：第 1 级升至第 2 级，生命/攻击/防御变为 **14300 / 2420 / 1320**。
- 精灵替换仓库可读取本地数据：**1 只精灵、18 个编队槽位**。
- 主线第 2–6 关逐关完成战斗、胜利结算、奖励发放和关卡推进；战斗模拟记录每关 4 回合、19 个步骤。
- 战斗动画图集 `atlas/combat/ani1.atlas` 的 8 帧资源已注册。
- 强制结束进程并在断网状态重新启动后，存档成功恢复：**1,109,500 金币、第 6 关进度、2 级精灵、普通点数 19,000、活动点数 4,000、18 个编队槽位**；重启后的主城界面显示已解锁到 1-7。

测试日志、UI 截图和 APK 均保存在 [Actions #110 → Artifacts](https://github.com/chenmoulaile/apk/actions/runs/45419753231)。我也检查了离线主城、战斗和重新启动后的截图。

## 下载与校验

最新通过断网验收的 APK：

- Actions 工件：`offline-apk-test-110`
- 文件：`super-spirit-ball-offline.apk`
- 大小：约 **120.2 MiB**
- SHA-256：`3af895efc1c76b39daae3dd856196241b470c62bcdb4a514b5233267777c65f7`

从 [Actions #110 → Artifacts](https://github.com/chenmoulaile/apk/actions/runs/45419753231) 下载 `offline-apk-test-110` 工件中的 APK。下载后可校验：

```bash
sha256sum super-spirit-ball-offline.apk
unzip -t super-spirit-ball-offline.apk
```

APK 使用本地测试签名，与原版签名不同。安装前需要先卸载原版；卸载可能清除原版应用数据。测试通过的环境是 Android 30 模拟器，尚不能据此保证所有真实设备都兼容。

## 实现范围与限制

- 登录、网络请求桩、本地玩家数据和存档由离线补丁提供。
- PvE 使用本地确定性战斗模拟器，敌方物种、等级和关卡配置取自恢复的游戏资源；伤害与技能结算并非原服务端战斗算法的完整复刻。
- 当前验收覆盖主城移动、精灵基础成长、精灵仓库读取、主线第 2–6 关、奖励和冷启动存档。
- 装备深度养成、道具使用、活动、副本、任务等仍需逐项恢复与验证。
- 排行榜、聊天、真实玩家、支付、广告、分享和在线服务不提供真实联网功能。

因此，当前版本已经可以作为**离线单机核心流程版本**游玩，但还不是完整复刻原版全部玩法。

## 资源与构建

- 原始 H5 资源已归档到 Release：`h5-source-20261123`（这是原始客户端资源包，不是离线 APK）。
- `work/tools/h5_snapshot.py`：恢复 H5 客户端和静态资源。
- `work/tools/patch_offline_h5.py`：离线登录、数据、存档与 PvE 补丁。
- `work/tools/patch_android.py`：Android WebView 本地入口改造。
- `work/tools/test_offline_apk.sh`：断网启动、成长、仓库、战斗、奖励和冷重启验收。
- `.github/workflows/offline-build.yml`：自动恢复/回退资源、重打包签名和模拟器验收。

后续修改必须继续以 `OFFLINE_SCENE_TEST=PASS` 的断网端到端结果为准，不要仅凭 APK 编译成功就标记通过。

## 当前回归状态

- [Actions #110](https://github.com/chenmoulaile/apk/actions/runs/45419753231)：**PASS**，已验证离线 JSON 存档恢复、18 个编队槽位、精灵成长、主线第 2–6 关、奖励和断网冷启动。
- [Actions #109](https://github.com/chenmoulaile/apk/actions/runs/45416971068)：**PASS**，已验证精灵仓库弹窗、主线第 2–6 关和冷启动存档。
- [Actions #108](https://github.com/chenmoulaile/apk/actions/runs/45407987560)：旧金币断言写成 1,099,500，而实际第 6 关存档为 1,109,500；模拟器行为已成功，工作流因断言不匹配而失败。
