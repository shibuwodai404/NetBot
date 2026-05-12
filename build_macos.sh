#!/usr/bin/env bash
# 一键打包：PyInstaller -> .app -> .dmg + .zip （macOS 专用）
# 用法： ./build_macos.sh
set -euo pipefail

cd "$(dirname "$0")"

VENV=".venv"
APP_NAME="NetBot"
BUNDLE_ID="com.lgyai.netbot"
DIST_DIR="dist"
BUILD_DIR="build"

# 检查 venv
if [[ ! -x "$VENV/bin/python" ]]; then
  echo "[!] 未发现 $VENV/bin/python，请先按 README 创建虚拟环境并安装依赖"
  exit 1
fi

echo "[*] 清理旧产物 ..."
rm -rf "$BUILD_DIR" "$DIST_DIR" "${APP_NAME}.spec"

echo "[*] 运行 PyInstaller ..."
"$VENV/bin/pyinstaller" \
  --name "$APP_NAME" \
  --windowed \
  --osx-bundle-identifier "$BUNDLE_ID" \
  --icon "assets/icons/NetBot.icns" \
  --add-data "assets:assets" \
  --noconfirm \
  --clean \
  --hidden-import psutil \
  --hidden-import icons \
  --hidden-import ui_macos \
  main.py

APP_PATH="$DIST_DIR/$APP_NAME.app"
PLIST="$APP_PATH/Contents/Info.plist"

if [[ ! -d "$APP_PATH" ]]; then
  echo "[!] 打包失败：找不到 $APP_PATH"
  exit 1
fi

echo "[*] 注入 LSUIElement = true（隐藏 Dock 图标，纯菜单栏 App）"
/usr/bin/plutil -replace LSUIElement -bool true "$PLIST" 2>/dev/null \
  || /usr/bin/plutil -insert LSUIElement -bool true "$PLIST"

# 修改 Info.plist 会让 PyInstaller 之前打的 ad-hoc 签名失效，
# 必须重新签一下，否则 macOS 会报 "invalid Info.plist" 并显示"已损坏"。
echo "[*] 重新 ad-hoc 签名（恢复修改 Info.plist 后失效的签名）..."
/usr/bin/codesign --force --deep --sign - "$APP_PATH"

# .dmg
DMG_ROOT="$BUILD_DIR/dmg_root"
DMG_PATH="$DIST_DIR/$APP_NAME.dmg"
echo "[*] 制作 $DMG_PATH ..."
rm -rf "$DMG_ROOT"
mkdir -p "$DMG_ROOT"
cp -R "$APP_PATH" "$DMG_ROOT/"
ln -s /Applications "$DMG_ROOT/Applications"
/usr/bin/hdiutil create \
  -volname "$APP_NAME" \
  -srcfolder "$DMG_ROOT" \
  -ov \
  -format UDZO \
  "$DMG_PATH" >/dev/null
rm -rf "$DMG_ROOT"

# .zip （用 ditto 保留 macOS 元数据，避免解压后丢权限）
ZIP_PATH="$DIST_DIR/$APP_NAME.zip"
echo "[*] 制作 $ZIP_PATH ..."
( cd "$DIST_DIR" && /usr/bin/ditto -c -k --sequesterRsrc --keepParent "$APP_NAME.app" "$APP_NAME.zip" )

echo ""
echo "[OK] 完成："
echo "    $APP_PATH"
echo "    $DMG_PATH        （推荐分发）"
echo "    $ZIP_PATH"
