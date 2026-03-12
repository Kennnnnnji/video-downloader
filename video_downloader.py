#!/usr/bin/env python3
"""视频下载器 - 支持哔哩哔哩 & 抖音"""

import os
import re
import sys
import shutil
from pathlib import Path

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QProgressBar,
    QTextEdit,
    QFileDialog,
    QMessageBox,
    QFrame,
)

import yt_dlp

__version__ = "1.0.1"

# ─── 主题 ───────────────────────────────────────────────

THEME = {
    "bg": "#F5F5F7",
    "surface": "#FFFFFF",
    "border": "#D2D2D7",
    "primary": "#007AFF",
    "primary_hover": "#0056CC",
    "primary_pressed": "#004499",
    "text": "#1D1D1F",
    "text_secondary": "#86868B",
    "success": "#34C759",
    "error": "#FF3B30",
    "warning": "#FF9500",
    "bilibili": "#FB7299",
    "douyin": "#161823",
}

STYLESHEET = f"""
QWidget {{
    font-family: -apple-system, "SF Pro Text", "Helvetica Neue", sans-serif;
    font-size: 14px;
    color: {THEME["text"]};
}}
QWidget#mainWindow {{
    background-color: {THEME["bg"]};
}}
QLabel#titleLabel {{
    font-size: 22px;
    font-weight: 700;
    color: {THEME["text"]};
}}
QLabel#versionLabel {{
    font-size: 12px;
    color: {THEME["text_secondary"]};
}}
QLabel#sectionLabel {{
    font-size: 13px;
    font-weight: 600;
    color: {THEME["text_secondary"]};
    margin-top: 6px;
}}
QLabel#platformBadge {{
    font-size: 12px;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 10px;
}}
QLabel#statusLabel {{
    font-size: 13px;
    color: {THEME["text_secondary"]};
}}
QLineEdit {{
    background-color: {THEME["surface"]};
    border: 1px solid {THEME["border"]};
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 14px;
    color: {THEME["text"]};
}}
QLineEdit:focus {{
    border-color: {THEME["primary"]};
}}
QLineEdit:disabled {{
    background-color: #F0F0F0;
    color: #999999;
    border-color: #E0E0E0;
}}
QComboBox {{
    background-color: {THEME["surface"]};
    border: 1px solid {THEME["border"]};
    border-radius: 8px;
    padding: 7px 12px;
    font-size: 14px;
    min-width: 140px;
}}
QComboBox:hover {{
    border-color: {THEME["primary"]};
}}
QComboBox:disabled {{
    background-color: #F0F0F0;
    color: #999999;
    border-color: #E0E0E0;
}}
QComboBox::drop-down {{
    border: none;
    width: 30px;
}}
QComboBox::down-arrow {{
    image: none;
    border: none;
}}
QComboBox QAbstractItemView {{
    background-color: {THEME["surface"]};
    border: 1px solid {THEME["border"]};
    border-radius: 8px;
    selection-background-color: {THEME["primary"]};
    selection-color: white;
    padding: 4px;
}}
QPushButton {{
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 14px;
    font-weight: 500;
}}
QPushButton#primaryBtn {{
    background-color: {THEME["primary"]};
    color: white;
    border: none;
    padding: 12px 24px;
    font-size: 15px;
    font-weight: 600;
}}
QPushButton#primaryBtn:hover {{
    background-color: {THEME["primary_hover"]};
}}
QPushButton#primaryBtn:pressed {{
    background-color: {THEME["primary_pressed"]};
}}
QPushButton#primaryBtn:disabled {{
    background-color: #B0B0B0;
    color: #FFFFFF;
}}
QPushButton#cancelBtn {{
    background-color: {THEME["error"]};
    color: white;
    border: none;
    padding: 12px 24px;
    font-size: 15px;
    font-weight: 600;
}}
QPushButton#cancelBtn:hover {{
    background-color: #E0352B;
}}
QPushButton#secondaryBtn {{
    background-color: {THEME["surface"]};
    color: {THEME["primary"]};
    border: 1px solid {THEME["border"]};
}}
QPushButton#secondaryBtn:hover {{
    background-color: #E8E8ED;
}}
QProgressBar {{
    background-color: #E5E5EA;
    border: none;
    border-radius: 4px;
    height: 8px;
    text-align: center;
}}
QProgressBar::chunk {{
    background-color: {THEME["primary"]};
    border-radius: 4px;
}}
QTextEdit#logArea {{
    background-color: {THEME["surface"]};
    border: 1px solid {THEME["border"]};
    border-radius: 8px;
    padding: 8px;
    font-family: "SF Mono", Menlo, Monaco, monospace;
    font-size: 12px;
    color: {THEME["text"]};
}}
QFrame#separator {{
    background-color: {THEME["border"]};
    max-height: 1px;
}}
"""

# ─── 平台识别 ──────────────────────────────────────────

PLATFORMS = {
    "bilibili": {
        "name": "哔哩哔哩",
        "color": THEME["bilibili"],
        "patterns": [
            r"bilibili\.com/video/",
            r"bilibili\.com/bangumi/",
            r"b23\.tv/",
            r"bilibili\.com",
        ],
    },
    "douyin": {
        "name": "抖音",
        "color": THEME["douyin"],
        "patterns": [
            r"douyin\.com",
            r"v\.douyin\.com/",
            r"iesdouyin\.com",
        ],
    },
}


def detect_platform(url: str) -> str | None:
    """根据 URL 识别平台，返回平台 key 或 None"""
    url = url.strip().lower()
    for key, info in PLATFORMS.items():
        for pattern in info["patterns"]:
            if re.search(pattern, url):
                return key
    return None


def extract_url(text: str) -> str:
    """从分享文本中提取视频链接（支持抖音/B站分享口令）"""
    text = text[:2048]
    urls = re.findall(r"https?://[^\s<>\"')\]\u4e00-\u9fff]+", text)
    # 优先返回能识别平台的链接
    for url in urls:
        url = url.rstrip("/.,;!?")
        if detect_platform(url):
            return url
    # 没有平台匹配时返回第一个 URL
    if urls:
        return urls[0].rstrip("/.,;!?")
    # 没有 URL，原样返回（可能是纯链接）
    return text.strip()


def normalize_url(url: str) -> str:
    """规范化 URL，处理特殊格式（如抖音 modal_id）"""
    url = url.strip()
    # 抖音: /jingxuan?modal_id=XXX, /discover?modal_id=XXX, /user/YYY?modal_id=XXX 等
    m = re.search(r"douyin\.com/.*[?&]modal_id=(\d+)", url)
    if m:
        video_id = m.group(1)
        return f"https://www.douyin.com/video/{video_id}"
    return url


def get_ffmpeg_location() -> str | None:
    """获取 ffmpeg 路径（打包后从 bundle 内加载）"""
    if getattr(sys, "frozen", False):
        # PyInstaller 打包环境
        base = sys._MEIPASS
        if os.path.isfile(os.path.join(base, "ffmpeg")):
            return base
    return None


# ─── 下载工作线程 ─────────────────────────────────────────

class DownloadWorker(QThread):
    """后台下载线程"""

    progress = pyqtSignal(float, str)   # 百分比, 消息
    log = pyqtSignal(str)               # 日志
    finished = pyqtSignal(bool, str)    # 成功?, 消息

    def __init__(self, url, output_dir, quality, fmt, cookies_browser):
        super().__init__()
        self.url = url
        self.output_dir = output_dir
        self.quality = quality
        self.fmt = fmt
        self.cookies_browser = cookies_browser
        pass

    def cancel(self):
        self.requestInterruption()

    def _progress_hook(self, d):
        if self.isInterruptionRequested():
            raise yt_dlp.utils.DownloadCancelled("用户取消下载")

        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            pct = (downloaded / total * 100) if total else 0

            speed = d.get("speed")
            speed_str = self._fmt_speed(speed)
            eta = d.get("eta")
            eta_str = self._fmt_eta(eta)

            msg = f"下载中... {speed_str}"
            if eta_str:
                msg += f"  |  剩余 {eta_str}"
            self.progress.emit(min(pct, 99.9), msg)

        elif d["status"] == "finished":
            self.progress.emit(100, "合并处理中...")
            filename = d.get("filename", "")
            if filename:
                self.log.emit(f"  文件: {Path(filename).name}")

    @staticmethod
    def _fmt_speed(speed):
        if not speed:
            return "计算中..."
        if speed < 1024:
            return f"{speed:.0f} B/s"
        if speed < 1024 * 1024:
            return f"{speed / 1024:.1f} KB/s"
        return f"{speed / 1024 / 1024:.1f} MB/s"

    @staticmethod
    def _fmt_eta(eta):
        if not eta:
            return ""
        if eta < 60:
            return f"{eta}秒"
        if eta < 3600:
            return f"{eta // 60}分{eta % 60}秒"
        return f"{eta // 3600}时{(eta % 3600) // 60}分"

    def _build_opts(self):
        opts = {
            "outtmpl": os.path.join(self.output_dir, "%(title)s.%(ext)s"),
            "progress_hooks": [self._progress_hook],
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "socket_timeout": 30,
        }

        # 画质
        fmt_map = {
            "best": "bestvideo+bestaudio/best",
            "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
            "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
            "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
        }

        if self.fmt == "audio":
            opts["format"] = "bestaudio/best"
            opts["postprocessors"] = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ]
        else:
            opts["format"] = fmt_map.get(self.quality, fmt_map["best"])
            opts["merge_output_format"] = "mp4"

        # 浏览器 Cookies
        if self.cookies_browser and self.cookies_browser != "none":
            opts["cookiesfrombrowser"] = (self.cookies_browser,)

        # 打包后使用内嵌 ffmpeg
        ffmpeg_loc = get_ffmpeg_location()
        if ffmpeg_loc:
            opts["ffmpeg_location"] = ffmpeg_loc

        return opts

    def run(self):
        try:
            url = normalize_url(self.url)
            if url != self.url:
                self.log.emit(f"链接已转换: {url}")
            self.log.emit(f"正在解析: {url}")
            opts = self._build_opts()

            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get("title", "未知标题")
                duration = info.get("duration")
                dur_str = ""
                if duration:
                    m, s = divmod(int(duration), 60)
                    dur_str = f" ({m}:{s:02d})"
                self.log.emit(f"标题: {title}{dur_str}")
                self.log.emit("开始下载...")

                if self.isInterruptionRequested():
                    self.finished.emit(False, "已取消")
                    return

                ydl.download([url])

            self.finished.emit(True, f"下载完成: {title}")

        except yt_dlp.utils.DownloadCancelled:
            self.finished.emit(False, "下载已取消")
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
        except Exception as e:
            if self.isInterruptionRequested():
                self.finished.emit(False, "下载已取消")
            else:
                self.log.emit(f"[错误详情] {e}")
                self.finished.emit(False, "下载出错，请检查链接是否有效")


# ─── 主窗口 ──────────────────────────────────────────────

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.setObjectName("mainWindow")
        self.setWindowTitle("视频下载器")
        self.setFixedSize(520, 760)
        self._init_ui()
        self._check_ffmpeg()

    def _check_ffmpeg(self):
        # 打包后 ffmpeg 已内嵌，无需检查
        if get_ffmpeg_location():
            return
        if not shutil.which("ffmpeg"):
            QMessageBox.warning(
                self,
                "缺少 FFmpeg",
                "未检测到 ffmpeg，视频合并功能将不可用。\n\n"
                "请通过 Homebrew 安装:\n"
                "  brew install ffmpeg",
            )

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(10)

        # ── 标题栏 ──
        header = QHBoxLayout()
        title = QLabel("视频下载器")
        title.setObjectName("titleLabel")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # 分隔线
        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep)

        # ── 视频链接 ──
        layout.addWidget(self._section_label("视频链接"))

        url_row = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("粘贴哔哩哔哩或抖音视频链接...")
        self.url_input.textChanged.connect(self._on_url_changed)
        url_row.addWidget(self.url_input)

        paste_btn = QPushButton("粘贴")
        paste_btn.setObjectName("secondaryBtn")
        paste_btn.setFixedWidth(60)
        paste_btn.clicked.connect(self._paste_url)
        url_row.addWidget(paste_btn)
        layout.addLayout(url_row)

        # 平台识别
        self.platform_label = QLabel("")
        self.platform_label.setObjectName("platformBadge")
        self.platform_label.setVisible(False)
        layout.addWidget(self.platform_label)

        # ── 下载选项 ──
        layout.addWidget(self._section_label("下载选项"))

        opts_row = QHBoxLayout()
        opts_row.setSpacing(12)

        # 画质
        q_col = QVBoxLayout()
        q_col.addWidget(self._mini_label("画质"))
        self.quality_combo = QComboBox()
        self.quality_combo.addItem("最佳画质", "best")
        self.quality_combo.addItem("1080p", "1080p")
        self.quality_combo.addItem("720p", "720p")
        self.quality_combo.addItem("480p", "480p")
        q_col.addWidget(self.quality_combo)
        opts_row.addLayout(q_col)

        # 格式
        f_col = QVBoxLayout()
        f_col.addWidget(self._mini_label("格式"))
        self.format_combo = QComboBox()
        self.format_combo.addItem("MP4 视频", "video")
        self.format_combo.addItem("MP3 音频", "audio")
        self.format_combo.currentIndexChanged.connect(self._on_format_changed)
        f_col.addWidget(self.format_combo)
        opts_row.addLayout(f_col)

        # Cookies
        c_col = QVBoxLayout()
        c_col.addWidget(self._mini_label("浏览器 Cookies"))
        self.cookies_combo = QComboBox()
        self.cookies_combo.addItem("不使用", "none")
        self.cookies_combo.addItem("Safari", "safari")
        self.cookies_combo.addItem("Chrome", "chrome")
        self.cookies_combo.addItem("Edge", "edge")
        self.cookies_combo.addItem("Firefox", "firefox")
        c_col.addWidget(self.cookies_combo)
        opts_row.addLayout(c_col)

        layout.addLayout(opts_row)

        # ── 下载位置 ──
        layout.addWidget(self._section_label("下载位置"))

        dir_row = QHBoxLayout()
        self.dir_input = QLineEdit()
        default_dir = str(Path.home() / "Downloads")
        self.dir_input.setText(default_dir)
        self.dir_input.setReadOnly(True)
        dir_row.addWidget(self.dir_input)

        browse_btn = QPushButton("浏览...")
        browse_btn.setObjectName("secondaryBtn")
        browse_btn.setFixedWidth(70)
        browse_btn.clicked.connect(self._browse_output)
        dir_row.addWidget(browse_btn)
        layout.addLayout(dir_row)

        # ── 下载按钮 ──
        layout.addSpacing(6)
        self.download_btn = QPushButton("开始下载")
        self.download_btn.setObjectName("primaryBtn")
        self.download_btn.setFixedHeight(44)
        self.download_btn.clicked.connect(self._start_download)
        layout.addWidget(self.download_btn)

        self.cancel_btn = QPushButton("取消下载")
        self.cancel_btn.setObjectName("cancelBtn")
        self.cancel_btn.setFixedHeight(44)
        self.cancel_btn.setVisible(False)
        self.cancel_btn.clicked.connect(self._cancel_download)
        layout.addWidget(self.cancel_btn)

        # ── 进度区域 ──
        layout.addSpacing(16)

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)

        # ── 日志区域 ──
        layout.addWidget(self._section_label("日志"))

        self.log_area = QTextEdit()
        self.log_area.setObjectName("logArea")
        self.log_area.setReadOnly(True)
        self.log_area.setFixedHeight(130)
        self.log_area.setPlaceholderText("等待操作...")
        layout.addWidget(self.log_area)

        # ── 底部打开文件夹按钮 ──
        self.open_folder_btn = QPushButton("打开下载文件夹")
        self.open_folder_btn.setObjectName("secondaryBtn")
        self.open_folder_btn.clicked.connect(self._open_folder)
        self.open_folder_btn.setVisible(False)
        layout.addWidget(self.open_folder_btn)

        # ── 页脚 ──
        footer = QLabel(f"v{__version__}  —  支持哔哩哔哩 & 抖音  |  基于 yt-dlp")
        footer.setObjectName("versionLabel")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(footer)

    @staticmethod
    def _section_label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("sectionLabel")
        return lbl

    @staticmethod
    def _mini_label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("font-size: 12px; color: #86868B; margin-bottom: 2px;")
        return lbl

    # ── 事件处理 ──

    def _on_url_changed(self, text: str):
        platform = detect_platform(text)
        if platform:
            info = PLATFORMS[platform]
            self.platform_label.setText(f"  {info['name']}  ")
            self.platform_label.setStyleSheet(
                f"background-color: {info['color']}; color: white; "
                f"font-size: 12px; font-weight: 600; "
                f"padding: 3px 10px; border-radius: 10px;"
            )
            self.platform_label.setVisible(True)
        else:
            self.platform_label.setVisible(False)

    def _on_format_changed(self, _index):
        is_audio = self.format_combo.currentData() == "audio"
        self.quality_combo.setEnabled(not is_audio)

    def _paste_url(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text:
            extracted = extract_url(text)
            self.url_input.setText(extracted)

    def _browse_output(self):
        path = QFileDialog.getExistingDirectory(
            self, "选择下载目录", self.dir_input.text()
        )
        if path:
            self.dir_input.setText(path)

    def _open_folder(self):
        path = self.dir_input.text()
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def _start_download(self):
        raw_text = self.url_input.text().strip()
        if not raw_text:
            QMessageBox.warning(self, "提示", "请输入视频链接")
            return

        # 从分享文本中提取链接
        url = extract_url(raw_text)
        if url != raw_text:
            self.url_input.setText(url)

        output_dir = self.dir_input.text()
        if not os.path.isdir(output_dir):
            QMessageBox.warning(self, "提示", "下载目录不存在")
            return

        # 切换 UI 状态
        self._set_downloading(True)
        self._log("─" * 40)
        self.progress_bar.setValue(0)
        self.open_folder_btn.setVisible(False)

        quality = self.quality_combo.currentData()
        fmt = self.format_combo.currentData()
        cookies = self.cookies_combo.currentData()

        self.worker = DownloadWorker(url, output_dir, quality, fmt, cookies)
        self.worker.progress.connect(self._on_progress)
        self.worker.log.connect(self._log)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _cancel_download(self):
        if self.worker and self.worker.isRunning():
            self._log("正在取消...")
            self.worker.cancel()
            self.cancel_btn.setEnabled(False)

    def _on_progress(self, pct: float, msg: str):
        self.progress_bar.setValue(int(pct))
        self.status_label.setText(msg)

    def _on_finished(self, success: bool, msg: str):
        self._set_downloading(False)
        if success:
            self._log(f"[完成] {msg}")
            self.status_label.setText(msg)
            self.status_label.setStyleSheet(f"color: {THEME['success']};")
            self.progress_bar.setValue(100)
            self.open_folder_btn.setVisible(True)
        else:
            self._log(f"[失败] {msg}")
            self.status_label.setText(msg)
            self.status_label.setStyleSheet(f"color: {THEME['error']};")
            self.progress_bar.setValue(0)

    def _set_downloading(self, active: bool):
        self.download_btn.setVisible(not active)
        self.cancel_btn.setVisible(active)
        self.cancel_btn.setEnabled(True)
        self.url_input.setEnabled(not active)
        self.format_combo.setEnabled(not active)
        self.cookies_combo.setEnabled(not active)
        self.progress_bar.setVisible(True)
        self.status_label.setVisible(True)
        if active:
            self.quality_combo.setEnabled(False)
            self.status_label.setStyleSheet(
                f"color: {THEME['text_secondary']};"
            )
        else:
            # 恢复画质选择器状态：音频模式下保持禁用
            is_audio = self.format_combo.currentData() == "audio"
            self.quality_combo.setEnabled(not is_audio)

    def _log(self, text: str):
        # 限制日志行数，防止内存膨胀
        if self.log_area.document().blockCount() > 500:
            cursor = self.log_area.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            cursor.movePosition(
                cursor.MoveOperation.Down, cursor.MoveMode.KeepAnchor, 100
            )
            cursor.removeSelectedText()
            cursor.deletePreviousChar()
        self.log_area.append(text)
        # 滚动到底部
        sb = self.log_area.verticalScrollBar()
        sb.setValue(sb.maximum())

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            if not self.worker.wait(3000):
                self.worker.terminate()
                self.worker.wait(1000)
        event.accept()


# ─── 入口 ───────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("视频下载器")
    app.setStyleSheet(STYLESHEET)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
