#!/usr/bin/env bash
# NetBot 一键安装 / 升级脚本（Linux）
#
# 已经装过的情况下再跑就是升级：脚本会先 kill 当前正在跑的实例，再装新版。
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

echo "[1/4] 下载 ${APP_NAME}-linux-${ARCH}.tar.gz ..."
curl -fL --progress-bar -o "$TAR_TMP" "$TAR_URL"

# 升级场景：杀掉正在跑的实例，避免装完一下子跑两份。
if pgrep -x "${APP_NAME}" >/dev/null 2>&1; then
  echo "[2/4] 检测到 ${APP_NAME} 正在运行，先退出 ..."
  pkill -x "${APP_NAME}" 2>/dev/null || true
  for _ in 1 2 3; do
    pgrep -x "${APP_NAME}" >/dev/null 2>&1 || break
    sleep 1
  done
  pkill -9 -x "${APP_NAME}" 2>/dev/null || true
else
  echo "[2/4] 无旧实例运行 ..."
fi

echo "[3/4] 解压到 ${INSTALL_DIR} ..."
mkdir -p "$INSTALL_DIR"
tar -xzf "$TAR_TMP" -C "$INSTALL_DIR"
chmod +x "${INSTALL_DIR}/${APP_NAME}"

echo "[4/4] 启动 NetBot（后台）..."
"${INSTALL_DIR}/${APP_NAME}" &

echo ""
echo "[OK] NetBot 已就绪：${INSTALL_DIR}/${APP_NAME}"
echo "    以后再跑同样的命令就是升级（会自动退掉旧版）。"
echo "    若托盘图标没出现，请确认桌面支持 AppIndicator："
echo "      sudo apt install libayatana-appindicator3-1 gir1.2-ayatanaappindicator3-0.1"
