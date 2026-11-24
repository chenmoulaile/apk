# 离线 APK

最新已验证的重打包、对齐并签名 APK：

- 文件：`super-spirit-ball-offline.apk`
- 体积：约 120 MiB
- SHA-256：`f3686b0aacef098f745322db97533a0e51db9c51ba9525aac87ae205d25e9490`
- 验收：Android 30 模拟器关闭 Wi-Fi/移动数据后安装、启动、主城移动、主线挑战、阵容、胜利结算、金币奖励，以及强制结束进程后的存档恢复均通过。

验收记录：[GitHub Actions run 45329870950](https://github.com/chenmoulaile/apk/actions/runs/45329870950)，Artifact 名称为 `offline-apk-test-67`。

当前 PvE 胜利响应由离线补丁本地构造，尚未完整复刻原服务端战斗回合 AI。稳定 APK 中的 `combat/ani1` 装饰动画仍有少量 `lost skin` 提示；主线进度和结算不受影响。当前 `main` 正在验证该特效的补丁，不要把未验证的新构建当成稳定版。APK 为本地测试签名；覆盖安装原版前需要先卸载原版。
