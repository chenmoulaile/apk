# 超级精灵球离线化研究

> 状态：静态分析已完成第一轮，云端动态探测正在执行；尚未形成可玩的离线 APK。原始 APK 已由用户上传到仓库根目录。

## 目录约定

- `work/`：分析记录、协议说明、工具脚本和后续源码修改。
- `dist/`：最终重打包 APK 的输出目录。
- `tmp/`：解包、反编译、抓包等临时文件，不提交临时内容。

## 当前结论

上传的 `com.ruirui.cjjlq.apk`（现已提交在仓库根目录） 是 QuickGame JS 壳，不是包含完整游戏客户端资源的独立 APK。启动入口指向远程 H5 页面：

`https://cjjlqres.ruiruiyouxi.com/taptapReleaseRes/index.html`

APK 本身未包含 HTML 页面或游戏 JS bundle。APK 内的 `assets/libQuickSDKH5_To_Client.js` 只暴露 QuickSDK 桥接契约。首轮确认的登录通知字段为 `status`、`uid`、`username`、`token`、`oaid`；这不是游戏网关的完整登录响应。

因此，只有这份 APK 还不足以构造能运行原游戏的离线版本。还需要原 H5 资源/本地缓存，或游戏运行时的请求与响应记录。协议说明见 [work/analysis/static-analysis.md](work/analysis/static-analysis.md)，桥接字段见 [work/protocol/quicksdk-bridge.json](work/protocol/quicksdk-bridge.json)。

## 约定

本项目的模拟玩家只用于离线本地的 AI/影子数据展示，并明确标注为模拟数据；不会伪装真实在线用户，也不会向外部排行榜注入虚假记录。离线付费能力应通过本地解锁/开发菜单实现，不连接真实支付渠道。

## 可重复分析工具

```bash
python3 work/tools/inspect_apk.py /path/to/com.ruirui.cjjlq.apk
python3 work/tools/dex_xref.py /path/to/com.ruirui.cjjlq.apk
python3 work/tools/make_login_notify.py --uid offline-local-001 --username "离线玩家"
```

第三个工具只生成已确认的 QuickSDK `loginNotify` 桥接输入（JSON 与 Base64），便于离线桥接测试；它不等于游戏网关登录响应，也没有被注入原 APK。

更完整的接口归属和交叉引用见 [work/analysis/sdk-endpoints.md](work/analysis/sdk-endpoints.md)。当前本地工作环境没有 APK 反编译/打包工具链；云端 Actions 已配置 Android SDK/模拟器探测流程。H5 资源是否能从旧入口恢复，须以动态探测产物为准，因此 `dist/` 暂无可验证的离线 APK。


## 云端动态探测

已增加 [Android emulator probe workflow](.github/workflows/android-probe.yml)。它会在 GitHub Actions Linux Runner 中创建 Android 30 x86_64 模拟器，尝试安装并启动仓库根目录的原始 APK，探测远程 H5 入口，并归档 Logcat、设备状态、可访问的应用数据和下载到的 H5 资源。

运行记录：
https://github.com/chenmoulaile/apk/actions/workflows/android-probe.yml

云端探测产物会在对应 workflow run 的 Artifacts 中保留 30 天。首次动态测试尚在执行，结果确认前不会宣称 APK 已能离线运行。
