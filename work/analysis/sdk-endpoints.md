# DEX 中可定位的 SDK 接口路径

本清单来自对原始 APK 的 DEX 字符串交叉引用，目的是区分第三方 SDK 请求与远程 H5 游戏自己的请求。路径本身不包含完整 URL、HTTP 方法、请求头、签名或响应结构。

## QuickSDK / QuickGame SDK

| 路径字符串 | 调用类与方法 | 归属判断 |
|---|---|---|
| `/v1/user/autoLogin` | `AccountLoginFragment.autoLoginByToken`、`ActiveFragment.autoLoginByToken`、`AutoLoginFragment.autoLoginByToken`、`SwitchAccountFragment.getAccount` | 渠道账号自动登录 |
| `/v1/user/loginByName` | `AccountLoginFragment.accountLogin`、`AutoLoginFragment.login` | 渠道账号密码登录 |
| `/v1/user/loginByPhone` | `AccountLoginFragment.phoneLogin` | 渠道手机登录 |
| `/v1/user/userLoginByOtherSdk` | `ThirdManager.thridLogin` | 第三方渠道登录 |
| `/v1/user/registerVisitor` | `LoginManager.slienceLogin`、`AccountLoginFragment.tryPlay` | 游客登录 |
| `/v1/user/registerUser` | `AccountRegisterFragment.register` | 渠道注册 |
| `/v1/auth/getUserInfo` | `LoginManager.requestQGUserExtraInfo` | 渠道用户扩展信息 |
| `/v1/auth/setGameRoleInfo` | `LoginManager.setGameRoleInfo` | 向渠道 SDK 上报游戏角色信息 |
| `/v1/auth/createOrder` | `QGPayManager.createOrder`、`QGPayManager.orderSDKCoins` | SDK 支付下单 |
| `/v1/auth/orderCancel` | `QGPayManager.postCancleOrder` | SDK 取消订单 |
| `/v1/auth/queryOrd` | `QGPayManager.requestPayResult`、`QGScanPayFragment.callPaySuccessForFiveTimes2` | SDK 支付结果查询 |
| `/v1/auth/walletInfo` | `QGPayManager.checkSDKCoins` | SDK 渠道币钱包查询 |
| `/v1/auth/logout` | `LoginManager.postSessionId` | 渠道 SDK 注销 |

SDK 的 IP 配置文件 `assets/quickgame_sdk/qg_ipconfig.txt` 内容为 `https://sdkapi-qg.ruiruiyouxi.com`。仍需在动态网络记录中确认每个请求实际拼接出的 host、method、headers、body 和响应。

## 其他 SDK 字符串

| 路径 | 调用位置 | 归属判断 |
|---|---|---|
| `/simulator/mobile/login` | `com.bytedance.bdtracker.v3.doInBackground` | 字节跳动统计/设备上报 SDK，不是游戏账号登录 |
| `/leaderboard/v1/*` | TapTap SDK 的 `com.taptap.sdk.common.network.NetworkClientKt.provideOkHttpClient` | TapTap SDK 排行榜路径常量；仅凭当前引用无法证明游戏 H5 通过它读写排名 |
| `/auth/v1/login-by-authorization-code`、`/auth/v1/login-by-token` | TapTap SDK login 代码与模型 | TapTap 平台授权，不是 H5 游戏网关响应 |

## 关于游戏自己的接口

当前没有发现包含游戏 H5 逻辑的本地 HTML/JS 文件；原生代码中也没有从上述 QuickSDK API 得到游戏资源/角色背包完整数据结构的证据。游戏自身 H5 页面可能在远程运行时再访问 `cjlq-gw.ruiruiyouxi.com` 或其他 API，但这个 APK 的静态内容不足以确认其请求契约。

下一步应对 H5 启动到角色进入游戏的实际请求做 HAR/PCAP/日志记录，再对每个响应字段逐项交叉引用；不要把 SDK 登录成功回调当作游戏登录成功。
