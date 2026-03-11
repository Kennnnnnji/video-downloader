#!/usr/bin/env python3
"""生成视频下载器应用图标"""

import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw


def draw_icon(size=1024):
    """绘制视频下载器图标"""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 圆角矩形背景 - 蓝紫渐变效果
    margin = int(size * 0.04)
    radius = int(size * 0.22)

    # 绘制渐变背景
    for y in range(margin, size - margin):
        ratio = (y - margin) / (size - 2 * margin)
        r = int(41 + (88 - 41) * ratio)
        g = int(128 + (86 - 128) * ratio)
        b = int(255 + (235 - 255) * ratio)
        draw.line([(margin, y), (size - margin, y)], fill=(r, g, b, 255))

    # 用圆角蒙版裁剪
    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=radius,
        fill=255,
    )
    bg = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    bg.paste(img, mask=mask)
    img = bg
    draw = ImageDraw.Draw(img)

    # 绘制下载箭头
    cx, cy = size // 2, size // 2 - int(size * 0.02)
    arrow_w = int(size * 0.18)
    arrow_h = int(size * 0.22)
    head_w = int(size * 0.30)
    head_h = int(size * 0.14)

    # 箭头杆
    shaft_top = cy - arrow_h
    shaft_bot = cy + int(size * 0.05)
    draw.rectangle(
        [cx - arrow_w // 2, shaft_top, cx + arrow_w // 2, shaft_bot],
        fill=(255, 255, 255, 240),
    )

    # 箭头头部（三角形）
    triangle_top = shaft_bot - int(size * 0.02)
    triangle_bot = triangle_top + head_h
    draw.polygon(
        [
            (cx - head_w, triangle_top),
            (cx + head_w, triangle_top),
            (cx, triangle_bot),
        ],
        fill=(255, 255, 255, 240),
    )

    # 底部横线（托盘）
    tray_y = triangle_bot + int(size * 0.06)
    tray_w = int(size * 0.30)
    tray_h = int(size * 0.04)
    draw.rounded_rectangle(
        [cx - tray_w, tray_y, cx + tray_w, tray_y + tray_h],
        radius=tray_h // 2,
        fill=(255, 255, 255, 200),
    )

    # 播放三角形（在箭头杆上方）
    play_cx = cx
    play_cy = shaft_top - int(size * 0.10)
    play_r = int(size * 0.09)
    draw.polygon(
        [
            (play_cx - int(play_r * 0.7), play_cy - play_r),
            (play_cx - int(play_r * 0.7), play_cy + play_r),
            (play_cx + play_r, play_cy),
        ],
        fill=(255, 255, 255, 230),
    )

    return img


def create_icns(output_dir: Path):
    """生成 .icns 文件"""
    icon_1024 = draw_icon(1024)

    iconset_dir = output_dir / "app_icon.iconset"
    iconset_dir.mkdir(exist_ok=True)

    sizes = [16, 32, 64, 128, 256, 512]
    for s in sizes:
        icon_1024.resize((s, s), Image.LANCZOS).save(
            iconset_dir / f"icon_{s}x{s}.png"
        )
        s2 = s * 2
        if s2 <= 1024:
            icon_1024.resize((s2, s2), Image.LANCZOS).save(
                iconset_dir / f"icon_{s}x{s}@2x.png"
            )

    icon_1024.save(iconset_dir / "icon_512x512@2x.png")

    icns_path = output_dir / "app_icon.icns"
    subprocess.run(
        ["iconutil", "-c", "icns", str(iconset_dir), "-o", str(icns_path)],
        check=True,
    )
    print(f"图标已生成: {icns_path}")

    # 清理 iconset 目录
    shutil.rmtree(iconset_dir)

    return icns_path


if __name__ == "__main__":
    create_icns(Path(__file__).parent)
