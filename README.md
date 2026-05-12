# NetBot

[![Build](https://github.com/shibuwodai404/NetBot/actions/workflows/build.yml/badge.svg)](https://github.com/shibuwodai404/NetBot/actions/workflows/build.yml)
[![Release](https://img.shields.io/github/v/release/shibuwodai404/NetBot?display_name=tag)](https://github.com/shibuwodai404/NetBot/releases)
[![License](https://img.shields.io/github/license/shibuwodai404/NetBot)](LICENSE)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-blue)

<p align="center">
  <img src="assets/icons/app/icon_ok_256.png"       alt="ok"       width="120" />
  <img src="assets/icons/app/icon_checking_256.png" alt="checking" width="120" />
  <img src="assets/icons/app/icon_error_256.png"    alt="error"    width="120" />
</p>

<p align="center"><sub>正常 · 检测中 · 异常</sub></p>

> A lightweight tray app that tells you which country your public IP is from, in real time.

NetBot 常驻菜单栏 / 系统托盘，实时显示当前公网 IP 的归属国家。适合代理 / VPN 用户随时确认「自己现在到底从哪里上网」。

支持 **🍎 macOS · 🐧 Linux · 🪟 Windows**。

---

## ✨ 它能干什么

- 一眼看到三字母国家码（`USA` / `CHN` / `JPN` / `SGP` ...）
- 三种状态：🟢 正常 · 🟡 检测中 / 切换中 · 🔴 异常
- 点开看完整 IP、城市、ISP、最后更新时间
- 切换 VPN / Wi-Fi 时立刻自动重新检测，不用等

---

## 📦 下载安装

### 🍎 macOS

**推荐：一键安装（零配置）**

```bash
curl -fsSL https://raw.githubusercontent.com/shibuwodai404/NetBot/main/install_macos.sh | bash
```

脚本会自动下载、绕过 Apple Gatekeeper 的 quarantine、安装到 `/Applications`、启动。完事后菜单栏右上角直接出图标。

<details>
<summary>手动安装（如果不放心跑别人的脚本）</summary>

1. 到 [Releases](../../releases) 下载 `NetBot.dmg`
2. 双击 `.dmg` → 把 `NetBot.app` 拖到 `Applications`
3. 终端跑一条命令撕掉 Apple 的 quarantine 标记：
   ```bash
   xattr -dr com.apple.quarantine /Applications/NetBot.app
   ```
   **这一步必须做。** 浏览器下载的未签名 App 会被 Apple 谎称"文件已损坏"，这是 Apple 政策不是 NetBot 的 bug。
4. 双击 NetBot.app

</details>

需要 macOS 11 Big Sur 及以上。

---

### 🐧 Linux

**一键安装：**

```bash
curl -fsSL https://raw.githubusercontent.com/shibuwodai404/NetBot/main/install_linux.sh | bash
```

系统需要 AppIndicator 支持（绝大多数桌面环境都有）：

```bash
sudo apt install libayatana-appindicator3-1 gir1.2-ayatanaappindicator3-0.1
```

GNOME 用户额外要装 [AppIndicator 扩展](https://extensions.gnome.org/extension/615/appindicator-support/)。

目前只构建 x86_64，ARM Linux 需要自己源码打包。

---

### 🪟 Windows

1. 到 [Releases](../../releases) 下载 `NetBot-windows-x64.zip`
2. 解压双击 `NetBot.exe`
3. 首次打开 SmartScreen 会弹"Windows 已保护你的电脑" → 点「更多信息」→「仍要运行」

需要 Windows 10 及以上。想开机自启，把 `NetBot.exe` 的快捷方式扔到 `shell:startup` 文件夹。

---

## 📜 License

[MIT](LICENSE)
