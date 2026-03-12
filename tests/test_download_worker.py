import unittest
from unittest.mock import patch

from PyQt6.QtCore import QCoreApplication
from yt_dlp.utils import DownloadError

import video_downloader


_APP = QCoreApplication.instance() or QCoreApplication([])


class _PermissionDeniedYDL:
    def __init__(self, _opts):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def extract_info(self, _url, download=False):
        raise DownloadError("permission denied while loading browser cookies")


class DownloadWorkerTest(unittest.TestCase):
    def test_cookies_permission_error_mentions_restart(self):
        messages = []
        worker = video_downloader.DownloadWorker(
            "https://www.douyin.com/video/123",
            "/tmp",
            "best",
            "video",
            "chrome",
        )
        worker.finished.connect(lambda success, msg: messages.append((success, msg)))

        with patch.object(video_downloader.yt_dlp, "YoutubeDL", _PermissionDeniedYDL):
            worker.run()

        self.assertEqual(messages, [(False, unittest.mock.ANY)])
        self.assertIn("重新打开应用", messages[0][1])


if __name__ == "__main__":
    unittest.main()
