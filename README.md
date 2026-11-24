# 超级精灵球离线化研究

> 当前状态：**离线主线 PvE 正在继续验证，尚未达到完整游戏复原或正式发布标准。**
>
> 最新代码提交：`313fac2`。GitHub Actions 离线构建/断网模拟器测试 #90 正在运行：
> [Build and test offline Android APK #90](https://github.com/chenmoulaile/apk/actions/runs/45380567773)。

## 已经由模拟器日志实测的能力

最近一次完整断网实测为 [Actions #89](https://github.com/chenmoulaile/apk/actions/runs/45378091812)。它的 APK 编译、重打包和签名步骤全部成功；最终端到端测试因为测试脚本在关卡 3 刚开始时就冷重启，未等关卡 4 完成，故整次工作流结论是 **FAIL**，不能把它当作通过验收的版本。

尽管如此，#89 的日志确实记录了以下真实行为：

- 关闭 Wi-Fi 和移动数据后，APK 使用本地 `file:///android_asset/game/index.html` 启动。
- 离线账号登录、进入主城、角色移动成功。
- 精灵升级请求成功，精灵属性由生命 13000、攻击 2200、防御 1200 提升至生命 14300、攻击 2420、防御 1320。
- 打开精灵仓库、关卡挑战、编队和战斗界面成功。
- 第 2、3 关的本地 PvE 战斗模拟、结算奖励和关卡推进均在日志中出现。
- `atlas/combat/ani1.atlas` 的 8 帧战斗动画资源成功注册。
- 强制结束进程并在断网状态重新启动后，存档恢复了 1,039,500 金币、第 3 关、升级后的精灵和道具数据。
- 日志中没有发现阻止主线流程的 JavaScript 异常或关键战斗资源加载失败。

#90 针对 #89 的测试时长问题，增加了第 2 至第 4 关逐关推进断言和进度截图；同时增加敌方编队完整性校验，避免敌方资源缺失时被错误判定为胜利。**这些最新改动仍以 #90 的实际运行结果为准。**

## 当前实现边界

- 本地登录、网络请求桩、本地玩家存档和部分基础 UI 行为由离线补丁提供。
- 当前 PvE 由本地确定性模拟器生成回合步骤；敌方物种和等级取自已恢复的游戏配置，但战斗伤害/技能处理是简化模型，并非原服务端战斗逻辑的完整复刻。
- 目前只覆盖已实测的主城移动、精灵基础成长/仓库交互和主线 PvE 路径。其他养成、装备、道具使用、活动、副本、任务等模块仍需逐项实现和测试。
- 在线玩家、排行榜、聊天、支付、广告、外部分享和联网服务不提供真实在线功能；场景中的训练对手是明确标记的本地模拟数据。
- 当前测试构建使用自动生成的本地签名，与原版签名不同；覆盖安装前需卸载原版。未通过最新断网验收的 APK 不应作为稳定版本分发。

## 最新构建与下载

请以 [Actions #90](https://github.com/chenmoulaile/apk/actions/runs/45380567773) 的结论和 Artifacts 为准。只有当工作流显示成功且日志中出现 `OFFLINE_SCENE_TEST=PASS` 时，才应把该工件视为通过当前主线离线验收的 APK。

较早的历史构建不代表当前 `main` 分支的代码与验证状态。

## 目录

- `work/analysis/`：APK 架构、资源依赖和静态分析结论。
- `work/analysis/game-protocol.md`：从原始客户端代码确认的 HTTP、WebSocket 和 Protobuf 契约。
- `work/protocol/`：协议摘录和配置格式记录。
- `work/recovered/`：H5 客户端资源快照脚本及清单；大体积资源通过 Actions Artifacts 保存。
- `work/tools/patch_offline_h5.py`：离线登录、网络桩、存档和 PvE 模拟补丁。
- `work/tools/patch_android.py`：Android APK/WebView 离线入口改造。
- `work/tools/test_offline_apk.sh`：断网启动、移动、精灵成长、主线 PvE、奖励和冷重启存档测试。
- `.github/workflows/offline-build.yml`：自动恢复 H5 资源、重打包签名 APK，并运行 Android 模拟器断网验收。

## 本地校验

下载 Actions Artifact 后，可校验 APK 完整性：

```bash
sha256sum super-spirit-ball-offline.apk
unzip -t super-spirit-ball-offline.apk
```
