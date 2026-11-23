# H5 游戏登录与 Protobuf 协议

> 来源：用户提供的 APK（原生壳）和从其内嵌 H5 入口下载的原始 Laya 客户端代码。
> 本文记录真实客户端代码中已确认的请求/响应契约。示例用户和本地数据并非抓包取得的真实账号数据。

## 0. 运行环境与渠道分支

H5 入口加载后，`code.js` 会打印：

```
当前渠道：TapTap
Game Version:1.0.1
```

该 APK 在 Android WebView 中实际选择 `Channel_NewWX`，而不是 `Channel_IOS` 的 `ios_h5` 分支。其关键环境逻辑：

- `Channel_NewWX.init()` 设置 `Env.POKE.GAME_ENV = "taptap"`。
- 只有 `window.rpenv == "wx"` 才设置 release；当前从 `taptapReleaseRes` 加载的运行路径符合 release。
- release 资源根目录：`https://cjjlqres.ruiruiyouxi.com/taptapReleaseRes/`。
- release 渠道登录号：`login_way=102`。
- `mix_way=4`。
- release 游戏 CGI 域名：`cjjlqwxweb.ruiruiyouxi.com`。
- 渠道系统字符串：`unknow`。
- H5 版本：`1.0.1`（和 APK 壳的 1.0.5 不同）。

不要混淆 `Channel_IOS`：那个独立分支在 `window.rpenv == "ios_h5"` 时选择，`mix_way=5`，不适用于本 APK 的 Android TapTap 路径。

## 1. HTTP 登录预阶段

客户端的 `NM.httpCmd(name, args)` 会自动补充参数：

- 已有本地登录缓存时，若 args 未提供 `sid`，会附加 `sid` 和 `token`；
- `login_way = Env.loginWay`；
- `envi = Env.isRelease ? 2 : 0`；
- `version = Env.version`（此包为 `1.0.1`）；
- `platform = Env.system`（TapTap NewWX 返回 `unknow`）；
- `mix_way = Env.mixWay`（TapTap NewWX 为 4）。

实际 URL 模板：

```
GET https://cjjlqwxweb.ruiruiyouxi.com/rp_web/{command}?{query}
```

### 1.1 服务器列表

请求：

```
GET /rp_web/svr_list?showOne=1&login_way=102&envi=2&version=1.0.1&platform=unknow&mix_way=4
```

`LoginModule.loadServerList()` 确认读取字段：

| 字段 | 用途 |
|---|---|
| `ret` | 0 时表示成功 |
| `svr_list` | 服务器区列表 |
| `in_white_list` | 白名单状态 |
| `login_svr_id_list` | 登录服务器 ID 列表 |
| `sid` | 回填 QuickSDK 登录态 user_id |
| `token` | 回填 QuickSDK 登录态 user_token |
| `submit_flag` | 等于 1 时标记受限城市 |
| `cvv` | 回填客户端 DM.cvv |
| `msg` | 失败提示 |

服务器列表项至少会被后续代码按 `zone_id`、`user_id` 访问；`user_id==0` 会走新角色注册路径，否则走已存在角色路径。

云端 Runner 对上述精确参数进行过只读请求。HTTP 状态为 200，但服务内容返回：

```json
{"msg":"system error","ret":-1}
```

因此当前可确认域名和路径可连通，但无法从该端点取得有效服务器列表。HTTP 200 不等于业务接口成功。没有自动请求 `regist`，避免在任何仍可用的服务端创建账号。

### 1.2 新角色注册（只提取，不自动执行）

当服务器区返回当前账号 `user_id==0`，客户端展示注册 UI，构造字段：

- `choicePetId = 3101`
- `zone_id = currentZone.zone_id`
- `oaid = QuickSdkMgr.getInstance().getOaid()`
- 用户输入 `name`、`sex`
- 可选分享字段：`inviter_user_id`、`inviter_zone_id`、`invite_type`、`share_id`、`share_img_id`

然后调用 `GET /rp_web/regist`。成功响应必须包含：

- `ret == 0`
- `sid`
- `token`
- `user_id`

此端点会创建或分配角色，属于有副作用操作；本次没有对线上服务调用它。

### 1.3 游戏服务器目录

`LoginModule.loadServerInfo()` 调用：

```
GET /rp_web/dir?zone_id={zone_id}&user_id={user_id}
```

如果带分享参数，还会附加 URL 编码的 `showData`。

成功响应字段：

- `ret == 0`
- `ip`：WebSocket 主机
- `port`：WebSocket 端口
- `city`：用于 `city < 3` 的受限城市标志
- `share_flag`：分享能力开关

### 1.4 城市等级

`LoginModule.loginInSocket()` 在 WebSocket 登录前调用 `GET /rp_web/ip_level`。成功时读取 `ret`、`level`，将 level 写入 `DM.cityLevel`。

## 2. WebSocket 二进制协议

客户端通过 Laya WebSocket 连接 `dir` 响应给出的 `ip:port`。

协议头固定 32 字节，大端序（BigEndian）：

| 偏移 | 长度 | 字段 | 类型 / 初始值 |
|---:|---:|---|---|
| 0 | 8 | `user_id` | uint64 |
| 8 | 4 | `cmd` | int32 |
| 12 | 4 | `body_len` | int32 |
| 16 | 8 | `start_mseconds` | uint64 |
| 24 | 4 | `magic_num` | int32，客户端默认 38183（0x9567） |
| 28 | 4 | `trans_id` | int32 |

32 字节头之后为 Protobuf body。请求/响应按 `cmd` 注册，异步响应还会通过 `trans_id` 匹配请求。

## 3. 登录 Protobuf

### 3.1 LoginReq

- CMD：16777219（`0x01000003`）
- 构造位置：`LoginModule.loginInSocket()`
- 客户端实际设置：`sid`、`token`、`cityLevel`、可选 `cvv`、分享字段。

字段：

| Proto 字段号 | 名称 | 类型 |
|---:|---|---|
| 1 | token | string |
| 2 | sid | string |
| 3 | loginWay | uint32 |
| 4 | platform | string |
| 5 | cityLevel | int32 |
| 6 | shareInfo | LoginShareInfo |
| 7 | shareId | int32 |
| 8 | shareImgId | int32 |
| 9 | machineBrand | string |
| 10 | machineModel | string |
| 11 | machineVersion | string |
| 12 | cvv | string |

`LoginShareInfo` 内有字段 `cardGenId`（int32，字段号 1）。

### 3.2 LoginRsp

- CMD：16777220（`0x01000004`）
- 客户端判断 `ret == 0` 成功。若非 0，登录流程清除缓存并中止。
- 该响应不是一个简单的“成功标志”：必须提供完整的 `userInfo` 快照，客户端后续初始化会马上解引用其多个子对象。

| Proto 字段号 | 名称 | 类型 |
|---:|---|---|
| 1 | ret | uint32 |
| 2 | userInfo | UserDataInfo |
| 3 | serverMtime | uint64 |
| 4 | loginNotice | LoginNotice |
| 5 | userLeadValue | repeated uint32 |
| 6 | offineInfo | OffineLineInfo |
| 7 | openSvrDays | int32 |
| 8 | openSvrTime | uint32 |
| 9 | mergeSvrDays | int32 |
| 10 | mergeSvrTime | uint32 |
| 11 | rawOpenSvrDays | uint32 |
| 12 | rawOpenSvrTime | uint32 |
| 13 | mergeSvrTimes | uint32 |
| 14 | openComeBackActivity | uint32 |
| 15 | goNewServerOld | bool |
| 16 | goNewServerNew | bool |
| 17 | newVersionFirstLoginTime | uint32 |

### 3.3 UserDataInfo

客户端 proto schema 定义的一级对象字段（完整字段名来自 `code.js` 的 Protobuf encoder/decoder）：

`baseInfo, extInfo, itemPackInfo, petPackInfo, petStorageInfo, sceneBagInfo, redotInfo, activityInfo, teamPkEffectInfo, relicInfo, shopInfo, hallInfo, monopolyInfo, assitPetPackInfo, treasureInfo, petBookInfo, titleInfo, happyBeachInfo, userGuildInfo, checkInfo, taskInfo, growthFound, petGrowTaskInfo, guideScheduleInfo, dailyConsumptionActivityInfo, rideInfo, commInfo, rankGameInfo, activityShopInfo, petRoomInfo, superHallInfo, guildMapInfo, guildImageSpiriteInfo, guildmapChallengetimes, chatBlacklistInfo, warCmdInfo, artifactBooksInfo, cashFundInfo, summerPetInfo, rechargeTurntableInfo, spriteSkinMapInfo, hasAddSkinModuleRedot, spriteSkinRedotInfo, srspiriteInfo, yearClbtInfo, headIconsInfo, specialActivityMap, userMazeInfo, advAwardInfo, partnerInfo, topAreaInfo, sharedCrystalInfo, warAreaInfo, endlessAbyssInfo, newSportsInfo, petCrystalInfo, newEquipCombine, newChampInfo, newSceneGradeInfo, timeSpaceCrackInfo, newStoreInfo, legendaryChallengeInfo, offerRewardInfo, eliteCallInfo, limitTimeAdvent, weekCircles, newVersionFixInfo, newTaskInfo, userDateAttrInfo, naturePowerInfo, collectCardInfo, checkInfo2, checkInfoCycle, mibaoPackInfo, mibaoLotteryInfo`

其中关键的 `baseInfo` 子对象字段：

`userId, name, sex, bornTime, oldTotalExp, oldNextLevelExp, level, vipLevel, zoneId, rankPlace, titleId, sceneLevel, sceneLevelTimes, avatarBits, avatarId, moneyInfo, wingId, pikachuId, totalFightScore, titleSubId, noticeId, vipExp, historyRecharge, loginWay, payIconValue, monthCardTime, firstPet, sid, hasFriendWish, liveCardTime, rideId, communicateSkillId, rankGradeInfo, platform, magicmapId, wan8VipSpecialAwardTime, lastPayTime, wan8Pf, operativeActivityAward, mixWay, pikaqiuFlag, trainMedalId, trainMedalLevel, trainMedalStar, iosCustomerFlag, userinfoDbreqTime, userinfoDbrspTime, svipExp, svipLevel, svipOverTime, svipFirstMonthFlag, headIcon, pointItemMap, realSex, totalFightScore_2, totalFightScore_3, dataVersion, newMonthCardTime, newLiveCardTime, totalExp, nextLevelExp, newVersionPlayer, newGuildAwardFlag, newPointItemMap, isPointTransform, weekCardTime, bubbleId, unlockBubbleBits, isAdvanceAccount, newUnlockBubbleBits, vipPackageId`

`moneyInfo` 中存在 `gold`、`diamond`、`cash`、`petCoin` 等货币字段，以及装备币、荣誉币、世界 Boss 币等货币字段。只写 `ret=0` 和空对象会令大量客户端初始化路径访问空值，不能视为足够的登录响应。

### 3.4 离线补充对象

`LoginNotice`：`title, nickName, content, name, date`。

`OffineLineInfo`：

- `second`：uint32
- `actionArr`：repeated Action
- `monthCardFlag`：bool
- `allLiveCardFlag`：bool

## 4. 进入主场景

`GameMain.enterScene()` 固定调用 `WorldManager.enterScene(1)`。

### EnterSceneReq

- CMD：16777221（`0x01000005`）
- 字段：`sceneId`（uint32，字段号 1），当前固定为 1。

### EnterSceneRsp

- CMD：16777222（`0x01000006`）

| Proto 字段号 | 名称 | 类型 |
|---:|---|---|
| 1 | ret | uint32 |
| 2 | sceneId | uint32 |
| 3 | userInfos | repeated UserSnapInfo |
| 4 | sceneBag | SceneBag |
| 5 | avengeUserId | uint64 |
| 6 | sceneName | string |

`SceneBag` 字段：`maxItemNum, curItemNum, maxSpiritNum, curSpiritNum, expCoinPercent, sceneLevelTimes, sceneLevel`。

在登录和进场完成后，客户端才注册 ChatModule、BagModule、MainUIModule，并显示主界面。因此构造完整离线登录至少要处理 LoginRsp、EnterSceneRsp、用户/背包/精灵数据和后续模块初始化请求。

## 5. 当前服务端可达性判断

只读请求 `/rp_web/svr_list` 在 release 域名返回 HTTP 200 / `ret=-1, msg="system error"`。所以：

- H5 静态资源服务器在线且可下载；
- 登录 CGI 域名 DNS 可解析、HTTP 可建立连接；
- 业务登录接口没有给出成功服务器清单；
- 没有调用会创建账号的 `/rp_web/regist`；
- 未取得真实的 LoginRsp 或玩家存档。

当前离线化难点在真正的游戏数据和 WebSocket RPC，不是 QuickSDK 的单一登录回调。

## 6. 已恢复的客户端资源

云端快照记录：

- 1,433 个文件，合计 89.1 MiB；
- `code.js`：11,670,591 bytes；
- `zip.txt`：2,564,527 bytes，zlib 解压后 29,443,820 bytes；
- 解压配置 JSON 包含 1,678 个 UI 配置项和数百份游戏配置表；
- 151 个资产引用返回 HTTP 404（路径和错误已列在 snapshot manifest）；
- 图集资源、主场景资源、图标和其他常用 UI 资源已下载。

这份数据属于 2026 年当前可访问的 H5 客户端，不等同于 10 多年前原始版本的旧游戏资源。应先以 APK 当前内嵌的 H5 URL 为准。

## 7. 未完成项

- 获取真正有效的服务器列表和 dir 返回数据；
- 确认 Android WebView 同意隐私后能否顺利进入登录界面；
- 取得真实 LoginRsp 或足够完整的字段依赖图；
- 构造本地 HTTP/WS 模拟服务，至少响应登录、进入场景和初始状态；
- 为关键游戏行为实现本地状态更新和 JSON/二进制存档；
- 重新打包、签名、安装并验证断网后可以启动和保存。

本报告不把模拟字段写成真实抓包结果。
