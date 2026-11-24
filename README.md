# 超级精灵球离线化研究

> 当前状态：**离线主线 PvE 已在断网模拟器中完整推进至第 4 关并验证冷启动存档；精灵仓库交互正在补做验证。项目尚未达到完整游戏复原或正式发布标准。**
>
> 当前代码：`dbc7ff7`。最新离线构建 #94 正在运行：
> [Build and test offline Android APK #94](https://github.com/chenmoulaile/apk/actions/runs/45385982857)。

## 已经由断网模拟器实测的能力

最近的完整主线断网实测为 [Actions #92](https://github.com/chenmoulaile/apk/actions/runs/45383112667)。这次工作流整体为 **FAIL**，但 APK 的重建、zipalign、签名成功，模拟器日志明确记录了以下功能：

- 关闭 Wi-Fi 和移动数据后，APK 通过本地 `file:///android_asset/game/index.html` 启动。
- 离线账号登录、进入主城、角色移动成功。
- 精灵升级成功，属性由生命 13000、攻击 2200、防御 1200 提升至生命 14300、攻击 2420、防御 1320。
- 主线第 2、3、4 关均完成本地 PvE 战斗：每关读取 4 个敌方槽位，产生 4 回合、19 个战斗步骤，胜利后发放对应奖励并逐关推进。
- `atlas/combat/ani1.atlas` 的 8 帧战斗动画资源成功注册。
- 强制结束进程并在断网状态重新启动后，成功恢复 1,069,500 金币、第 4 关、2 级精灵及道具数据（普通点数 4000、活动点数 2000）。
- 未发现阻止主线流程的 JavaScript 异常或战斗资源 `Failed to load` 错误。

#92 的失败仅发生在精灵仓库入口测试：自动化脚本使用了错误的触屏坐标，实际没有打开替换/仓库弹窗，因此没有触发 `GetPetStorageRsp`。后续通过原始 `client/res/ui.json` 核对了 UI 布局尺寸（720×1280）与模拟器屏幕（1080×1920）的 1.5 倍缩放，修正了替换按钮和弹窗关闭按钮坐标。**这项交互以 #94 的断网模拟器实测结果为准。**

更早的 [Actions #89](https://github.com/chenmoulaile/apk/actions/runs/45378091812) 只推进并持久化到第 3 关，不能作为第 4 关的验收依据。

## 当前实现边界

- 本地登录、网络请求桩、本地玩家存档和部分基础 UI 行为由离线补丁提供。
- 当前 PvE 由本地确定性模拟器生成回合步骤；敌方物种和等级取自已恢复的游戏配置，但伤害、技能处理是简化模型，并非原服务端战斗逻辑的完整复刻。
- 已实测范围是主城移动、精灵基础成长、主线 PvE 第 2–4 关奖励和冷启动存档。精灵仓库交互正在复验；装备、道具使用、活动、副本、任务等模块仍需逐项实现和测试。
- 在线玩家、排行榜、聊天、支付、广告、外部分享和联网服务不提供真实在线功能；场景中的训练对手是明确标记的本地模拟数据。
- 当前测试构建使用自动生成的本地签名，与原版签名不同；覆盖安装前需卸载原版。未通过最新断网验收的 APK 不应作为稳定版本分发。

## 最新构建与下载

请以 [Actions #94](https://github.com/chenmoulaile/apk/actions/runs/45385982857) 的结论和 Artifacts 为准。只有当工作流显示成功且日志中出现 `OFFLINE_SCENE_TEST=PASS` 时，才应把该工件视为通过当前主线离线验收的 APK。

较早的历史构建不代表当前 `main` 分支的代码与验证状态。

## 目录

- `work/analysis/`：APK 架构、资源依赖和静态分析结论。
- `work/analysis/game-protocol.md`：从原始客户端代码确认的 HTTP、WebSocket 和 Protobuf 契约。
- `work/protocol/`：协议摘录和配置格式记录。
- `work/recovered/`：H5 客户端资源快照脚本及清单；大体积资源通过 Actions Artifacts 保存。
- `work/tools/patch_offline_h5.py`：离线登录、网络桩、存档和 PvE 模拟补丁。
- `work/tools/patch_android.py`：Android APK/WebView 离线入口改造。
- `work/tools/test_offline_apk.sh`：断网启动、移动、精灵成长、仓库 UI、主线 PvE、奖励和冷重启存档测试。
- `.github/workflows/offline-build.yml`：自动恢复 H5 资源、重打包签名 APK，并运行 Android 模拟器断网验收。

## 本地校验

下载 Actions Artifact 后，可校验 APK 完整性：

```bash
sha256sum super-spirit-ball-offline.apk
unzip -t super-spirit-ball-offline.apk
```
