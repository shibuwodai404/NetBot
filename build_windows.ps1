# 一键打包：PyInstaller -> Windows .exe + .zip
# 用法（在 Windows PowerShell 里）： .\build_windows.ps1
# 或在 GitHub Actions windows-latest 上自动执行
$ErrorActionPreference = 'Stop'
Set-Location -Path $PSScriptRoot

$VENV = ".venv"
$APP_NAME = "NetBot"
$DIST_DIR = "dist"
$BUILD_DIR = "build"

# 准备虚拟环境
if (-not (Test-Path "$VENV\Scripts\python.exe")) {
    Write-Host "[*] 创建虚拟环境 ..."
    python -m venv $VENV
}

Write-Host "[*] 安装依赖 ..."
& "$VENV\Scripts\python.exe" -m pip install --upgrade pip --quiet
& "$VENV\Scripts\pip.exe" install -r requirements.txt --quiet

Write-Host "[*] 清理旧产物 ..."
Remove-Item -Recurse -Force $BUILD_DIR, $DIST_DIR, "$APP_NAME.spec" -ErrorAction SilentlyContinue

Write-Host "[*] 运行 PyInstaller ..."
& "$VENV\Scripts\pyinstaller.exe" `
    --name $APP_NAME `
    --onefile `
    --windowed `
    --noconfirm `
    --clean `
    --hidden-import psutil `
    --hidden-import pystray._win32 `
    --hidden-import ui_pystray `
    --hidden-import icons_pil `
    main.py

$EXE_PATH = "$DIST_DIR\$APP_NAME.exe"
if (-not (Test-Path $EXE_PATH)) {
    Write-Error "[!] 打包失败：找不到 $EXE_PATH"
    exit 1
}

# 打 zip
$ZIP_PATH = "$DIST_DIR\$APP_NAME-windows-x64.zip"
Write-Host "[*] 制作 $ZIP_PATH ..."
Compress-Archive -Path $EXE_PATH -DestinationPath $ZIP_PATH -Force

Write-Host ""
Write-Host "[OK] 完成："
Write-Host "    $EXE_PATH"
Write-Host "    $ZIP_PATH"
