#!/bin/bash
set -euo pipefail

APP_NAME="VideoDownloader"
SCRIPT="video_downloader.py"
ICON="app_icon.icns"
BUNDLE_ID="com.videodownloader.app"

cd "$(dirname "$0")"

echo "==> 创建虚拟环境..."
python3 -m venv .venv
source .venv/bin/activate

echo "==> 安装依赖..."
pip install -r requirements.txt
pip install pyinstaller

echo "==> 生成图标..."
python gen_icon.py

echo "==> 检测 ffmpeg..."
FFMPEG_PATH=$(which ffmpeg 2>/dev/null || true)
FFPROBE_PATH=$(which ffprobe 2>/dev/null || true)
ADD_BINARY_FLAGS=""
if [ -n "$FFMPEG_PATH" ] && [ -n "$FFPROBE_PATH" ]; then
    echo "    ffmpeg:  $FFMPEG_PATH"
    echo "    ffprobe: $FFPROBE_PATH"
    ADD_BINARY_FLAGS="--add-binary $FFMPEG_PATH:. --add-binary $FFPROBE_PATH:."
else
    echo "    [警告] 未找到 ffmpeg/ffprobe，打包后将无法合并视频"
fi

echo "==> 打包应用..."
pyinstaller \
    --name "$APP_NAME" \
    --windowed \
    --noconfirm \
    --clean \
    --icon "$ICON" \
    --osx-bundle-identifier "$BUNDLE_ID" \
    --strip \
    $ADD_BINARY_FLAGS \
    "$SCRIPT"

echo "==> 创建发布 zip..."
cd dist && zip -r -y "${APP_NAME}.zip" "${APP_NAME}.app"

echo ""
echo "构建完成!"
echo "  应用: dist/${APP_NAME}.app"
echo "  发布包: dist/${APP_NAME}.zip"
