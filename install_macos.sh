#!/usr/bin/env bash
# NetBot 一键安装 / 升级脚本（macOS）
#
# 通过 curl 下载（不会被 Apple 加 quarantine 标记），自动安装到 /Applications，
# 撕掉任何遗留的 quarantine 标记，最后启动 NetBot。
#
# 已经装过的情况下再跑就是升级：脚本会先退出当前正在跑的实例，再装新版。
#
# 用法（任选一种）：
#   ① 一行搞定：
#      curl -fsSL https://raw.githubusercontent.com/shibuwodai404/NetBot/main/install_macos.sh | bash
#
#   ② 下载后再执行（更安全，可先审查脚本）：
#      curl -fsSL https://raw.githubusercontent.com/shibuwodai404/NetBot/main/install_macos.sh -o install.sh
#      bash install.sh

set -euo pipefail

REPO="shibuwodai404/NetBot"
APP_NAME="NetBot"
DMG_URL="https://github.com/${REPO}/releases/latest/download/${APP_NAME}.dmg"
TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/netbot.XXXXXX")"
DMG_TMP="${TMP_DIR}/${APP_NAME}.dmg"
APP_DEST="/Applications/${APP_NAME}.app"

cleanup() { rm -rf "$TMP_DIR"; }
trap cleanup EXIT

echo "[1/5] 下载最新版 ${APP_NAME}.dmg ..."
curl -fL --progress-bar -o "$DMG_TMP" "$DMG_URL"

# 升级场景：检测到 NetBot 已经在跑就先优雅退出。
# macOS .app 是单实例 —— 不退掉的话最后那行 `open` 只会把旧进程切到前台，新代码不生效。
if pgrep -x "${APP_NAME}" >/dev/null 2>&1; then
  echo "    检测到 ${APP_NAME} 正在运行，先退出 ..."
  pkill -x "${APP_NAME}" 2>/dev/null || true
  # 等最多 3 秒让它清理；还活着就 SIGKILL
  for _ in 1 2 3; do
    pgrep -x "${APP_NAME}" >/dev/null 2>&1 || break
    sleep 1
  done
  pkill -9 -x "${APP_NAME}" 2>/dev/null || true
fi

echo "[2/5] 挂载 DMG ..."
MOUNT_OUTPUT=$(/usr/bin/hdiutil attach -nobrowse "$DMG_TMP")
MOUNT_POINT=$(echo "$MOUNT_OUTPUT" | awk -F'\t' '/\/Volumes\//{print $NF; exit}')
if [[ -z "${MOUNT_POINT}" || ! -d "${MOUNT_POINT}/${APP_NAME}.app" ]]; then
  echo "[!] 挂载失败或镜像里找不到 ${APP_NAME}.app"
  exit 1
fi

echo "[3/5] 安装到 ${APP_DEST} ..."
rm -rf "$APP_DEST"
cp -R "${MOUNT_POINT}/${APP_NAME}.app" /Applications/
/usr/bin/hdiutil detach "$MOUNT_POINT" -quiet

echo "[4/5] 撕掉 quarantine 标记 ..."
/usr/bin/xattr -dr com.apple.quarantine "$APP_DEST" 2>/dev/null || true

echo "[5/5] 启动 NetBot ..."
open "$APP_DEST"

echo ""
echo "[OK] NetBot 已就绪：$APP_DEST"
echo "    几秒后菜单栏右上角应出现图标。"
echo "    以后再跑同样的命令就是升级（会自动退掉旧版）。"
