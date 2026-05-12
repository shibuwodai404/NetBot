#!/usr/bin/env bash
# NetBot 一键安装脚本（Linux）
#
# 用法：
#   curl -fsSL https://raw.githubusercontent.com/shibuwodai404/NetBot/main/install_linux.sh | bash

set -euo pipefail

REPO="shibuwodai404/NetBot"
APP_NAME="NetBot"
ARCH=$(uname -m)
INSTALL_DIR="${HOME}/.local/bin"

TAR_URL="https://github.com/${REPO}/releases/latest/download/${APP_NAME}-linux-${ARCH}.tar.gz"
# 用 mktemp -d 避免 GNU mktemp 对 -t 的不同解释
TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/netbot.XXXXXX")"
TAR_TMP="${TMP_DIR}/${APP_NAME}.tar.gz"

cleanup() { rm -rf "$TMP_DIR"; }
trap cleanup EXIT

echo "[1/3] 下载 ${APP_NAME}-linux-${ARCH}.tar.gz ..."
curl -fL --progress-bar -o "$TAR_TMP" "$TAR_URL"

echo "[2/3] 解压到 ${INSTALL_DIR} ..."
mkdir -p "$INSTALL_DIR"
tar -xzf "$TAR_TMP" -C "$INSTALL_DIR"
chmod +x "${INSTALL_DIR}/${APP_NAME}"

echo "[3/3] 启动 NetBot（后台）..."
"${INSTALL_DIR}/${APP_NAME}" &

echo ""
echo "[OK] NetBot 已安装到 ${INSTALL_DIR}/${APP_NAME}"
echo "    若托盘图标没出现，请确认桌面支持 AppIndicator："
echo "      sudo apt install libayatana-appindicator3-1 gir1.2-ayatanaappindicator3-0.1"
