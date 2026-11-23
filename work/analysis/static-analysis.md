# APK 静态分析记录

## 输入文件与可复现指纹

- 文件：`com.ruirui.cjjlq.apk`（现已上传并提交到仓库根目录）
- 大小：21,675,613 bytes
- SHA-256：`ffdaeee37a4d67a69f98c107dce913d4a58fe2ecbcaa8b809fe94b6a542dbf6b`
- APK ZIP 条目：1,027
- DEX：`classes.dex` 9,268,240 bytes；`classes2.dex` 5,497,576 bytes
- 包名：`com.ruirui.cjjlq`
- versionCode / versionName：`6 / 1.0.5`
- minSdk / targetSdk：`21 / 34`

以上均从上传 APK 的 ZIP 内容和二进制 AndroidManifest.xml 读取。

## 客户端架构

Manifest 的 application 类为 `com.qk.plugin.js.shell.GameApplication`。启动 Activity 是 `com.qk.plugin.js.shell.SplashActivity`，主要游戏容器是 `com.qk.plugin.js.shell.MainActivity`。

在 `classes.dex` 的 `Lcom/qk/plugin/js/shell/MainActivity;` 构造方法中可找到：

```
https://cjjlqres.ruiruiyouxi.com/taptapReleaseRes/index.html
libQuickSDK_v2.js
libSDK.js
libQuickSDKH5_To_Client.js
libSDK_To_Client.js
```

APK ZIP 中没有任何 `.html` / `.htm` 游戏文件，也没有除 SDK 桥接及其广告/SDK资源之外的游戏 JS bundle。APK 内的 `assets/libQuickSDKH5_To_Client.js` 是 QuickSDK H5-to-native 桥接脚本，不是游戏本体。

因此这份 APK 是“原生壳 + 远程 H5 游戏页面”的打包，不是完整本地游戏。仅替换登录响应不能恢复它：必须先取得 H5 的 HTML、JS、配置和图片/音频/图集资源，再找出游戏网关所需接口。

## 已确认的远程域名

| 用途 | APK 中发现的地址 | 证据 |
|---|---|---|
| H5 游戏入口 | `https://cjjlqres.ruiruiyouxi.com/taptapReleaseRes/index.html` | MainActivity 构造方法中的常量字符串 |
| 发现的域名常量 | `https://cjlq-gw.ruiruiyouxi.com/` | DEX 交叉引用定位到 `com.ruirui.cjjlq.wxapi.WXEntryActivity.shareToWechatMiniGame`；目前不能认定为游戏 API 基址 |
| QuickGame SDK IP 配置 | `https://sdkapi-qg.ruiruiyouxi.com` | `assets/quickgame_sdk/qg_ipconfig.txt` |

对 H5 入口和上述域名根地址的外部访问尝试未能获得网页内容；当前运行环境的 DNS 查询也失败。尚不能确认服务是否仍在线、域名是否已停用或仅当前环境无法解析。

## DEX 字符串交叉引用结果（已定位调用类/方法）

通过扫描 DEX 指令中的 `const-string` / `const-string-jumbo` 引用，将路径字符串定位到包含它们的类和方法。详细复现脚本为 `work/tools/dex_xref.py`。

| 字符串 | 引用位置 | 可得结论 |
|---|---|---|
| `https://cjjlqres.ruiruiyouxi.com/taptapReleaseRes/index.html` | `com.qk.plugin.js.shell.MainActivity.<init>` | 原生壳的 H5 入口 URL |
| `https://cjlq-gw.ruiruiyouxi.com/` | `com.ruirui.cjjlq.wxapi.WXEntryActivity.shareToWechatMiniGame` | 位于微信小游戏分享代码；不是已证实的游戏 HTTP API |
| `/v1/user/autoLogin` | QuickSDK 的 `AccountLoginFragment.autoLoginByToken`、`ActiveFragment.autoLoginByToken`、`AutoLoginFragment.autoLoginByToken`、`SwitchAccountFragment.getAccount` | 渠道 SDK 账号自动登录 |
| `/v1/user/loginByName` | QuickSDK 的 `AccountLoginFragment.accountLogin`、`AutoLoginFragment.login` | 渠道 SDK 账号登录 |
| `/v1/user/userLoginByOtherSdk` | QuickSDK 的 `ThirdManager.thridLogin` | 第三方渠道登录 |
| `/v1/user/registerVisitor` | QuickSDK 的 `LoginManager.slienceLogin`、`AccountLoginFragment.tryPlay` | QuickSDK 游客登录 |
| `/v1/auth/getUserInfo` | QuickSDK 的 `LoginManager.requestQGUserExtraInfo` | SDK 用户扩展信息 |
| `/v1/auth/setGameRoleInfo` | QuickSDK 的 `LoginManager.setGameRoleInfo` | SDK 角色信息上报 |
| `/v1/auth/createOrder` | QuickSDK 的 `QGPayManager.createOrder`、`orderSDKCoins` | SDK 支付下单 |
| `/simulator/mobile/login` | `com.bytedance.bdtracker.v3.doInBackground` | 字节跳动统计 SDK 路径，不是游戏账号登录 |
| `/leaderboard/v1/...` | TapTap SDK 的 `com.taptap.sdk.common.network.NetworkClientKt.provideOkHttpClient` 中有路径常量引用 | TapTap SDK 排行榜集成线索；不能证明是游戏自有排行榜协议 |

这轮交叉引用说明：DEX 里确实存在不少登录和排名路径，但它们分属 QuickSDK、ByteDance 统计和 TapTap SDK。仅凭这些常量不能拼出 H5 游戏本身的登录请求/响应。游戏 H5 自己的 API 仍然未知。

## QuickSDK 登录桥接协议（已确认）

源文件：`assets/libQuickSDKH5_To_Client.js`

1. `QuickSDK.init(productCode, productKey, debug, callback)` 将 `debug` 保存到对象，并通过 native bridge 调用 `webDidLoad`。
2. `QuickSDK.login(callback)` 保存游戏侧回调函数，然后调用 native bridge 的 `login` 动作。
3. 原生端回调进入 `CallbackFromAndroid(string)`，随后调用 `CallbackFromIOS(string)`。
4. `CallbackFromIOS` 对传入字符串执行 `base64_decode` 并 JSON parse，根据顶层 `action` 分发。
5. 当 `action == "loginNotify"` 时，桥接层从 `callData.data` 读取以下字段：

| 字段 | 代码用途 | 证据状态 |
|---|---|---|
| `status` | 登录是否成功，赋给回调顶层 `status` | 明确读取 |
| `uid` | 用户 ID | 明确读取 |
| `username` | 用户名 | 明确读取 |
| `token` | 用户 token | 明确读取 |
| `oaid` | 设备 OAID | 明确读取 |
| `status_key` | 当 status 不为 true 时作为 message | 明确读取 |
| `channel_type` | 从 `QuickSDK.quickData.channel_type` 读取，用于回调顶层和 data 内的 `channelId` | 明确引用；quickData 的填充流程还需完整动态跟踪 |

输出到游戏侧的结构（根据桥接代码整理；值为占位符，不是抓到的真实数据）：

```json
{
  "status": true,
  "channelId": "<QuickSDK.quickData.channel_type>",
  "data": {
    "uid": "<callData.data.uid>",
    "username": "<callData.data.username>",
    "token": "<callData.data.token>",
    "isLogin": true,
    "channelId": "<QuickSDK.quickData.channel_type>",
    "oaid": "<callData.data.oaid>",
    "message": "登录成功"
  }
}
```

特别注意：脚本无论 `callData.data.status` 是 true 还是 false，都会把 `data.isLogin` 写成 true；真正的成功状态由回调顶层 `status` 体现。这是桥接实现的实际行为，不应把 `isLogin` 单独当成服务端成功凭据。

传给 `CallbackFromAndroid` 的字符串是 base64 编码的 JSON；其外层形式例如：

```json
{
  "action": "loginNotify",
  "data": {
    "status": true,
    "uid": "local-user-1",
    "username": "Offline Player",
    "token": "local-session",
    "oaid": "",
    "status_key": ""
  }
}
```

这是用于解释结构的本地示例，不是已捕获的历史响应，也不代表游戏服务器的协议。

## QuickSDK 角色数据契约（已确认）

`QuickSDK.uploadGameRoleInfo(roleInfo, callback)` 要求 roleInfo 至少包含：

- `isCreateRole`
- `serverId`
- `serverName`
- `userRoleId`
- `userRoleName`
- `userRoleBalance`
- `vipLevel`
- `userRoleLevel`
- `partyName`

其中 `vipLevel`、`userRoleBalance`、`userRoleLevel` 被脚本检查为整数。随后桥接层增加以下别名字段：

- `gameRoleName = userRoleName`
- `gameRoleId = userRoleId`
- `gameUserBalance = userRoleBalance`
- `gameUserLevel = userRoleLevel`

再调用 native bridge 的 `updateRole`。这只是渠道 SDK 的角色上报参数，不是游戏网关返回的角色存档。

## QuickSDK 支付桥接契约（已确认）

`QuickSDK.pay(orderInfo, callback)` 要求订单含：

`productCode, goodsId, uid, userRoleId, userRoleName, userServer, userLevel, quantifier, count, cpOrderNo, amount, subject, desc, callbackUrl, extrasParams`

脚本另外检查 uid、userRoleId、userRoleName、userServer、userLevel 非空，amount 可解析为数字，subject 非空。它将 `subject/desc/cpOrderNo/userServer` 等转成 native SDK 对应字段，再以 `{roleInfo, orderInfo}` 结构调起支付。

`payNotify` 的已读取字段是 `status`、`channelOrderNo`、`cpOrderNo`、`extarsParams`（源码拼写如此）、`message`。

离线版本不应调用真实支付。适合采用明确标注的本地开发菜单/本地解锁，并把解锁状态写进本地存档；不能声称这构成真实内购。

## 不能据现有 APK 得出的结论

DEX 中还包含 TapTap SDK 的授权和排行榜路径，例如：

- `/auth/v1/login-by-authorization-code`
- `/auth/v1/login-by-token`
- `/leaderboard/v1/user-centered-friend-scores`
- `/leaderboard/v1/user-centered-top-scores`
- `/leaderboard/v1/user-scores`

这些字符串属于集成 SDK 的线索，不能据此认定它们就是本游戏网关的登录/排名接口。APK 没有显示实际 HTTP 请求的完整 URL、参数、签名、请求头、返回 JSON schema；也没有抓包 HAR/PCAP、TLS 解密日志或运行缓存。因此不能负责任地编造所谓完整登录响应包、用户信息、货币、道具和背包字段。

## 下一步依赖

要继续协议级逆向和离线化，需要至少一个下列来源：

1. 旧手机/模拟器中该 App 的 WebView 缓存或完整应用数据备份；
2. 旧版本的 H5 资源目录（index.html、入口 JS、配置 JSON、资源清单及关联资源）；
3. 曾经运行该游戏时保存的 Charles/mitmproxy/HttpCanary 抓包或日志；
4. 另一份仍能打开该游戏的安装包/渠道包，或已导出的游戏资源包。

收到这些材料后，按“游戏启动 → 渠道登录 → 游戏网关登录 → 玩家档案 → 配置/道具 → 存档读写”逐步还原，不跳过未确认字段。

## 当前构建环境与状态

本次环境中没有检测到 `apktool`、`jadx`、`aapt/aapt2`、`d8`、`smali`、`adb`、`gradle` 或 `zipalign`。尝试从网络下载工具时 DNS 无法解析，因此没有完成反编译/重打包工具链安装。仓库当前仅提交静态分析和可重复的 Python 检查脚本，`dist/` 尚无 APK。没有执行过设备运行测试或安装测试。

## 仓库规则

- `work/` 保存分析、协议文档、源码和构建脚本。
- `tmp/` 保存解包、日志和中间文件，不提交。
- `dist/` 保存最终离线 APK。


## 云端动态分析状态（2026-11-23）

原始 APK 已提交到仓库根目录 `com.ruirui.cjjlq.apk`。GitHub Actions workflow `.github/workflows/android-probe.yml` 使用 Ubuntu 托管 Runner、KVM 和 Android 30 x86_64 模拟器；它会下载远程 H5 入口、安装/启动 APK，并归档 logcat、设备截图、WebView 状态及可访问的应用数据。

当前有效的测试运行记录：
https://github.com/chenmoulaile/apk/actions/runs/45174334881

先前没有 KVM 配置的两次任务已取消；第 3 次任务已成功完成 KVM 权限步骤，并进入模拟器启动/安装阶段。此记录不等于 APK 已经安装成功；应以后续 Actions 结果和 Artifacts 为准。
