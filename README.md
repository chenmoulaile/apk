# 超级精灵球离线化

> 当前状态：**核心单机主线已通过第 6 关的断网模拟器验收。** 最新通过版本为 [Actions #109](https://github.com/chenmoulaile/apk/actions/runs/45416971068)，测试日志包含 `OFFLINE_SCENE_TEST=PASS`。

## 已通过的断网功能

在 Android 30 模拟器关闭 Wi-Fi 和移动数据后，最新 APK 完成了以下端到端测试：

- 从 APK 内本地 H5 入口启动：`file:///android_asset/game/index.html`。
- 离线登录并进入主城，角色移动正常。
- 精灵成长：第 1 级升至第 2 级，生命/攻击/防御变为 **14300 / 2420 / 1320**。
- 打开精灵替换仓库，成功读取本地仓库数据：**1 只精灵、18 个编队槽位**；关闭弹窗后返回精灵页面。
- 主线第 2–6 关逐关战斗、胜利结算、奖励和关卡推进均通过。每关配置 4 个敌方槽位，模拟战斗生成 4 回合、19 个步骤。
- 战斗动画图集 `atlas/combat/ani1.atlas` 的 8 帧资源已注册。
- 强制结束进程并在断网状态重新启动后，存档恢复：**1,109,500 金币、第 6 关、2 级精灵、普通点数 19,000、活动点数 4,000**。

以上结果由 [Actions #109](https://github.com/chenmoulaile/apk/actions/runs/45416971068) 的完整模拟器日志和截图验证；工作流结论为成功。

## 下载与校验

最新通过验收的 APK：

- Actions 工件：`offline-apk-test-109`
- 文件：`super-spirit-ball-offline.apk`
- 大小：约 120.2 MiB
- SHA-256：`19f28131dd0ba42161b38e0d2326b52edc2f1e31786f3fed215795595cccdffa`

可从 [Actions #106 → Artifacts](https://github.com/chenmoulaile/apk/actions/runs/45405123352) 下载 APK。下载后可校验：

```bash
sha256sum super-spirit-ball-offline.apk
unzip -t super-spirit-ball-offline.apk
```

APK 使用本地测试签名，与原版签名不同。安装前需要先卸载原版；卸载会清除原版应用本地数据。

## 实现范围与限制

- 登录、网络请求桩、本地玩家数据和存档由离线补丁提供。
- PvE 使用本地确定性战斗模拟器，敌方物种/等级读取恢复的游戏配置；伤害与技能结算并非原服务端战斗算法的完整复刻。
- 已验收范围是主城移动、精灵基础成长、精灵仓库读取、主线第 2–6 关、奖励和冷启动存档。
- 装备深度养成、道具使用、活动、副本、任务等仍需逐项恢复与验证。
- 排行榜、聊天、真实玩家、支付、广告、分享和在线服务不提供真实联网功能。

## 资源与构建

- 原始 H5 资源已归档到 Release：`h5-source-20261123`（这是原始客户端资源包，不是离线 APK）。
- `work/tools/h5_snapshot.py`：恢复 H5 客户端和静态资源。
- `work/tools/patch_offline_h5.py`：离线登录、数据、存档与 PvE 补丁。
- `work/tools/patch_android.py`：Android WebView 本地入口改造。
- `work/tools/test_offline_apk.sh`：断网启动、成长、仓库、战斗、奖励和冷重启验收。
- `.github/workflows/offline-build.yml`：自动恢复/回退资源、重打包签名和模拟器验收。

后续修改应继续以 `OFFLINE_SCENE_TEST=PASS` 的断网端到端结果为准，不要仅凭 APK 编译成功就标记通过。

## 当前回归状态

- [Actions #109](https://github.com/chenmoulaile/apk/actions/runs/45416971068)：**PASS**，已验证精灵仓库弹窗、18 个编队槽位、本地仓库读取、主线第 2–4 关和冷启动存档。
- [Actions #108](https://github.com/chenmoulaile/apk/actions/runs/45407987560)：仓库与主线第 2–6 关的模拟器行为均成功；工作流只因旧金币断言写成 1,099,500，而实际第 6 关存档为 1,109,500，故结论为 FAIL。
- [Actions #109](https://github.com/chenmoulaile/apk/actions/runs/45416971068)：已修正两处金币断言，正在重跑完整构建与断网模拟器回归。

