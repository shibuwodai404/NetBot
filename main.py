"""
NetBot 入口分发器
根据运行平台选择 UI 后端：
  - macOS: rumps（菜单栏支持文字 + 图标并列，原生体验最好）
  - Windows / Linux: pystray + PIL（把国家码画进图标）

可通过环境变量 NETBOT_UI=pystray 强制使用跨平台后端
（便于在 macOS 上调试 Win/Linux 路径）。
"""

import os
import sys


def main():
    forced = os.environ.get("NETBOT_UI", "").strip().lower()

    if forced == "pystray" or sys.platform != "darwin":
        from ui_pystray import run_app
    else:
        from ui_macos import run_app

    run_app()


if __name__ == "__main__":
    main()
