#!/usr/bin/env bash
# 一键打包：PyInstaller -> Linux 可执行 + tar.gz
# 用法： ./build_linux.sh    （在 Linux 系统上运行；或 GitHub Actions ubuntu-latest）
#
# 系统依赖（首次运行需手动装）：
#   sudo apt-get install -y libayatana-appindicator3-1 gir1.2-ayatanaappindicator3-0.1
# 没装也能跑，但托盘图标可能不出现（依赖桌面环境是否支持 AppIndicator）
set -euo pipefail

cd "$(dirname "$0")"

VENV=".venv"
APP_NAME="NetBot"
DIST_DIR="dist"
BUILD_DIR="build"

# 准备虚拟环境
if [[ ! -x "$VENV/bin/python" ]]; then
  echo "[*] 创建虚拟环境 ..."
  python3 -m venv "$VENV"
fi

echo "[*] 安装依赖 ..."
"$VENV/bin/pip" install --quiet --upgrade pip
"$VENV/bin/pip" install --quiet -r requirements.txt

echo "[*] 清理旧产物 ..."
rm -rf "$BUILD_DIR" "$DIST_DIR" "${APP_NAME}.spec"

echo "[*] 运行 PyInstaller ..."
"$VENV/bin/pyinstaller" \
  --name "$APP_NAME" \
  --onefile \
  --windowed \
  --noconfirm \
  --clean \
  --hidden-import psutil \
  --hidden-import pystray._xorg \
  --hidden-import pystray._appindicator \
  --hidden-import PIL._tkinter_finder \
  --hidden-import ui_pystray \
  --hidden-import icons_pil \
  main.py

BIN_PATH="$DIST_DIR/$APP_NAME"
if [[ ! -x "$BIN_PATH" ]]; then
  echo "[!] 打包失败：找不到 $BIN_PATH"
  exit 1
fi

# tar.gz 分发包（保留可执行权限）
ARCH=$(uname -m)
TAR_NAME="${APP_NAME}-linux-${ARCH}.tar.gz"
echo "[*] 制作 $DIST_DIR/$TAR_NAME ..."
( cd "$DIST_DIR" && tar -czf "$TAR_NAME" "$APP_NAME" )

echo ""
echo "[OK] 完成："
echo "    $BIN_PATH"
echo "    $DIST_DIR/$TAR_NAME"
