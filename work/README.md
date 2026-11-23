# 工作目录说明

- `analysis/`：APK 架构、资源依赖和反编译结论。
- `protocol/`：仅收录从 APK 源码中实际确认的桥接字段；未确认的网关响应不能猜。
- `tools/`：可重复运行的静态检查工具。
- 后续应用源码修改保存在本目录，不覆盖原始 APK。
- 临时解包输出放在 `../tmp/`，最终签名 APK 放在 `../dist/`。

## 检查原始 APK

```bash
python3 work/tools/inspect_apk.py /path/to/com.ruirui.cjjlq.apk
```

当前没有 H5 游戏源文件，因此此阶段不产生“可玩的离线 APK”。
