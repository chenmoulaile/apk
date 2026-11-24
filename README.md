# 超级精灵球离线化研究

> 当前状态：**核心离线主线 PvE 已通过 Android 30 断网模拟器自动验收**。最新已验证 APK 对应 GitHub Actions run [45327605989](https://github.com/chenmoulaile/apk/actions/runs/45327605989)，结果为 `OFFLINE_SCENE_TEST=PASS`。

## 已验证能力

- APK 将原远程 H5 入口改为 `file:///android_asset/game/index.html`，核心游戏资源随 APK 本地加载。
- 在关闭 Wi-Fi 和移动数据后，能够初始化本地账号、进入主城并移动角色。
- 能打开主线挑战、阵容和战斗结算界面。
- 本地 PvE 响应能返回胜利、发放金币并推进关卡；最近一次测试从关卡 1 连续推进到关卡 4，金币增加到 1,030,000。
- 本地账号数据使用 localStorage/protobuf 保存。后续构建会增加强制结束进程后的冷启动恢复验收。

## 当前实现边界

当前 PvE 战斗响应由离线补丁本地构造，自动返回胜利并驱动原版结算 UI；它还不是原服务端战斗 AI/回合协议的完整重实现。排行榜、真实在线玩家、支付、广告和外部分享不连接服务器；排行榜展示的模拟玩家会明确标识为模拟数据。

目前仍有少量非核心资源待完善：战斗辅助特效的部分皮肤帧曾出现 Laya `lost skin` 提示，部分音乐资源此前缺失。资源扫描器现已增加音乐文件自动发现，并把常用音效和战斗 `ani1` 图集加入构建门槛。少量启动阶段的 QuickSDK 原生回调竞态仍会打印一次 ReferenceError，但不会阻止离线主流程；验收脚本只忽略这一条已知启动日志。

## 最新构建产物

- 已验证 APK：GitHub Actions [offline-apk-test-65](https://github.com/chenmoulaile/apk/actions/runs/45327605989) 的 Artifacts。
- APK 文件：`dist/super-spirit-ball-offline.apk`。
- SHA-256：`1633987a65902b07fc3b107150ac0f0ce1b24cd822cef21bd0e3bf0066808cb6`。
- H5 资源快照：GitHub Actions [recovered-h5-client-24](https://github.com/chenmoulaile/apk/actions/runs/45327606038) 的 Artifacts。

## 目录

- `work/`：分析记录、协议说明、资源扫描和补丁工具。
- `dist/`：签名后的离线 APK 与校验和。
- `.github/workflows/offline-build.yml`：重建 APK、关闭网络、执行自动化主线验收。
- `work/tools/test_offline_apk.sh`：主城移动、主线挑战、战斗、奖励及冷重启验收脚本。

## 本地校验

```bash
sha256sum -c dist/SHA256SUMS.txt
```

APK 使用 Actions 生成的本地测试签名。它是独立安装包；若设备已有同包名但不同签名的原版安装，需要先卸载原版再安装此 APK。