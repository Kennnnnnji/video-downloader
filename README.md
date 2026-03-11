# 视频下载器 VideoDownloader

macOS 桌面应用，支持下载哔哩哔哩和抖音视频。基于 yt-dlp + PyQt6 构建，原生 macOS 风格界面。

![macOS](https://img.shields.io/badge/macOS-13%2B-blue) ![Python](https://img.shields.io/badge/Python-3.10%2B-green) ![License](https://img.shields.io/badge/License-GPL%20v3-red)

## 功能

- **哔哩哔哩** — 支持普通视频、番剧、短链接 (b23.tv)
- **抖音** — 支持视频页、分享口令、精选页 modal_id 链接
- **画质选择** — 最佳 / 1080p / 720p / 480p
- **格式切换** — MP4 视频 / MP3 纯音频
- **浏览器 Cookies** — 支持 Safari / Chrome / Firefox，解决登录限制
- **自动平台识别** — 粘贴链接即时显示平台标签
- **分享口令解析** — 直接粘贴抖音/B站分享文本，自动提取链接
- **内嵌 ffmpeg** — 打包版零依赖，解压即用

## 截图

<p align="center">
  <img src="https://via.placeholder.com/520x760/F5F5F7/1D1D1F?text=VideoDownloader" alt="App Screenshot" width="400">
</p>

> 替换为实际截图: 运行 app 后 `Cmd+Shift+4` 截图，放入仓库后更新路径。

## 安装

### 方式一：下载预构建版本（推荐）

前往 [Releases](../../releases) 下载最新 `VideoDownloader.zip`，解压后双击 `VideoDownloader.app` 即可运行。

> 首次打开可能提示"无法验证开发者"，请前往 **系统设置 → 隐私与安全性 → 仍要打开**。

### 方式二：从源码运行

```bash
git clone https://github.com/Kennnnnnji/video-downloader.git
cd video-downloader

# 创建虚拟环境并安装依赖
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 运行
python video_downloader.py
```

**前置要求：**
- Python 3.10+
- ffmpeg（用于视频合并）：`brew install ffmpeg`

## 从源码构建 .app

```bash
chmod +x build.sh
./build.sh
```

构建完成后：
- `dist/VideoDownloader.app` — 可直接运行的应用
- `dist/VideoDownloader.zip` — 可分发的压缩包

构建脚本会自动检测并内嵌系统中的 ffmpeg/ffprobe，打包后无需额外安装。

## 使用说明

1. **粘贴链接** — 复制视频链接或分享口令，点击"粘贴"按钮
2. **选择选项** — 画质、格式、是否使用浏览器 Cookies
3. **开始下载** — 点击"开始下载"，进度条实时显示速度和剩余时间
4. **打开文件夹** — 下载完成后可直接打开下载目录

### 关于浏览器 Cookies

部分视频需要登录才能下载（如 B 站会员视频），选择对应浏览器后，程序会自动读取该浏览器的登录状态。

### 支持的链接格式

| 平台 | 格式示例 |
|------|---------|
| 哔哩哔哩 | `https://www.bilibili.com/video/BVxxxxxx` |
| 哔哩哔哩 | `https://b23.tv/xxxxxx` |
| 抖音 | `https://www.douyin.com/video/xxxxxx` |
| 抖音 | `https://v.douyin.com/xxxxxx/` |
| 抖音分享 | `7@5.com 08/24 �mu+ ...https://v.douyin.com/xxx/` |

## 技术栈

| 组件 | 技术 |
|------|------|
| GUI | PyQt6 |
| 下载引擎 | yt-dlp |
| 视频处理 | ffmpeg (内嵌) |
| 打包 | PyInstaller |
| 图标生成 | Pillow |

## 项目结构

```
video-downloader/
├── video_downloader.py   # 主程序（GUI + 下载逻辑）
├── gen_icon.py            # 应用图标生成器
├── build.sh               # 一键构建脚本
├── requirements.txt       # Python 依赖
├── app_icon.icns          # 应用图标
└── README.md
```

## License

GPL v3
