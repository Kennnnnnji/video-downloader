# 视频下载器 - 添加 Edge Cookies 支持

## 概述

为视频下载器添加 Microsoft Edge 浏览器的 cookies 获取支持，并改进 cookies 获取失败时的用户提示。

## 背景

当前应用支持 Safari、Chrome、Firefox 三种浏览器的 cookies 获取功能，但缺少对 Microsoft Edge 的支持。Edge 在 macOS 用户群体中有一定使用量，应当支持。

此外，cookies 获取失败时提示信息不够明确，用户不知道如何解决权限问题。

## 设计方案

### 1. 添加 Edge 浏览器支持

**文件**: `video_downloader.py`

**位置**: UI 初始化部分，cookies 下拉框（约第 520-524 行）

**改动**:
```python
# 改动前
self.cookies_combo.addItem("不使用", "none")
self.cookies_combo.addItem("Safari", "safari")
self.cookies_combo.addItem("Chrome", "chrome")
self.cookies_combo.addItem("Firefox", "firefox")

# 改动后
self.cookies_combo.addItem("不使用", "none")
self.cookies_combo.addItem("Safari", "safari")
self.cookies_combo.addItem("Chrome", "chrome")
self.cookies_combo.addItem("Edge", "edge")
self.cookies_combo.addItem("Firefox", "firefox")
```

**说明**: `yt-dlp` 原生支持 `edge` 参数，无需额外逻辑。

### 2. 改进错误提示

**文件**: `video_downloader.py`

**位置**: `DownloadWorker.run()` 方法中的异常处理（约第 410-415 行）

**改动**:
```python
# 改动前
except yt_dlp.utils.DownloadError as e:
    msg = str(e)
    if "login" in msg.lower() or "cookie" in msg.lower():
        self.finished.emit(False, "需要登录，请选择浏览器 Cookies 后重试")
    else:
        self.finished.emit(False, f"下载失败: {msg}")

# 改动后
except yt_dlp.utils.DownloadError as e:
    msg = str(e)
    if "login" in msg.lower() or "cookie" in msg.lower() or "permission" in msg.lower():
        self.finished.emit(False,
            "获取浏览器 Cookies 失败。\n"
            "请确保：\n"
            "1. 已在浏览器中登录抖音\n"
            "2. 系统设置 → 隐私与安全性 → 完全磁盘访问 → 添加本应用\n"
            "3. 配置完成后，请完全退出并重新打开应用"
        )
    else:
        self.finished.emit(False, f"下载失败: {msg}")
```

**说明**:
- 新增 `permission` 关键词检测
- 提示信息明确说明解决步骤，并提示授权后重启应用

## 影响范围

- 仅修改 `video_downloader.py` 一个文件
- 不影响现有功能
- 向后兼容

## 测试要点

1. 选择 Edge 浏览器，确保 cookies 能正确传递给 yt-dlp
2. 模拟权限不足场景，验证提示信息正确显示且包含重启提示
3. 验证其他浏览器选项仍正常工作
