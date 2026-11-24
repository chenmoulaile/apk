# 超级精灵球离线化研究

> 当前状态：**核心离线主线 PvE 已通过 Android 30 断网模拟器验收，并通过进程冷重启后的存档恢复测试。** 已验证稳定 APK 对应 GitHub Actions run [45329870950](https://github.com/chenmoulaile/apk/actions/runs/45329870950)，结果为 `OFFLINE_SCENE_TEST=PASS`。

## 已验证能力

- APK 将原远程 H5 入口改为 `file:///android_asset/game/index.html`，游戏核心资源随 APK 本地加载。
- 在关闭 Wi-Fi 和移动数据后，能够初始化本地账号、进入主城并移动角色。
- 能打开主线挑战、阵容和战斗结算界面。
- 本地 PvE 响应能返回胜利、发放金币并推进关卡；测试从关卡 1 连续推进到关卡 4，金币增加到 1,030,000。
- 测试随后强制结束 APK 进程，并在保持断网的情况下重新启动；Logcat 确认恢复了 `1,030,000` 金币和第 `4` 关，重启截图也显示 103 万金币和 1-5 挑战入口。
- 声音配置扫描已补齐常用音效，已验证的 APK 中包含 `res/music/20001.wav` 与 `res/music/20019.wav`。

## 当前实现边界

当前 PvE 战斗响应由离线补丁本地构造，自动返回胜利并驱动原版结算 UI；它还不是原服务端战斗 AI/回合协议的完整重实现。排行榜、真实在线玩家、支付、广告和外部分享不连接服务器；排行榜展示的模拟玩家会明确标识为模拟数据。

稳定 APK 中仍有一项非致命视觉问题：战斗辅助特效 `combat/ani1` 的部分帧会出现 Laya `lost skin` 提示，不影响胜利结算或存档。当前 `main` 分支的后续提交 `c11f19a` 正在尝试修复这组动画帧的初始化顺序，尚未通过新一轮模拟器验证。少量启动阶段的 QuickSDK 原生回调竞态仍会打印一次 `CallbackFromAndroid` ReferenceError，但不会阻止离线主流程。

## 最新已验证 APK

- GitHub Actions run：[45329870950](https://github.com/chenmoulaile/apk/actions/runs/45329870950)。
- Artifact：`offline-apk-test-67`。
- APK：`dist/super-spirit-ball-offline.apk`，约 120 MiB。
- SHA-256：`f3686b0aacef098f745322db97533a0e51db9c51ba9525aac87ae205d25e9490`。
- H5 资源快照：[recovered-h5-client-26](https://github.com/chenmoulaile/apk/actions/runs/45329870899)。

请从对应 Actions run 的 Artifacts 下载 APK。APK 使用 Actions 生成的本地测试签名；它与原版签名不同，覆盖安装前需要先卸载原版。

## 目录

- `work/`：分析记录、协议说明、资源扫描和补丁工具。
- `dist/`：最终 APK 的输出目录（构建产物保存在 Actions Artifacts）。
- `.github/workflows/offline-build.yml`：重建 APK、断网安装、主线战斗与冷重启存档验收。
- `work/tools/test_offline_apk.sh`：主城移动、主线挑战、战斗、奖励及冷重启验收脚本。

## 本地校验

下载 Actions Artifact 后，可用以下命令校验 APK 完整性：

```bash
sha256sum super-spirit-ball-offline.apk
unzip -t super-spirit-ball-offline.apk
```
