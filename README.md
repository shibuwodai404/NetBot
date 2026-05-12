# NetBot

[![Build](https://github.com/shibuwodai404/NetBot/actions/workflows/build.yml/badge.svg)](https://github.com/shibuwodai404/NetBot/actions/workflows/build.yml)
[![Release](https://img.shields.io/github/v/release/shibuwodai404/NetBot?display_name=tag)](https://github.com/shibuwodai404/NetBot/releases)
[![License](https://img.shields.io/github/license/shibuwodai404/NetBot)](LICENSE)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-blue)

<p align="center">
  <img src="assets/icons/app/icon_ok_256.png"       alt="ok"       width="100" />
  <img src="assets/icons/app/icon_ok_risk_256.png"  alt="ok_risk"  width="100" />
  <img src="assets/icons/app/icon_checking_256.png" alt="checking" width="100" />
  <img src="assets/icons/app/icon_error_256.png"    alt="error"    width="100" />
</p>

<p align="center"><sub>正常 · 隐私风险 · 检测中 · 异常</sub></p>

> A lightweight tray app that tells you which country your public IP is from, in real time — with built-in privacy leak checks.

NetBot 常驻菜单栏 / 系统托盘，实时显示当前公网 IP 的归属国家，并主动检测 DNS / IPv6 / IP 信誉 / 地理一致性等 **隐私泄露信号**。适合代理 / VPN 用户随时确认「自己现在到底从哪里上网，以及暴露了什么」。

支持 **🍎 macOS · 🐧 Linux · 🪟 Windows**。

---

## ✨ 它能干什么

- 一眼看到三字母国家码（`USA` / `CHN` / `JPN` / `SGP` ...）
- 四种状态用机器人姿势 / 形状区分，不靠颜色（详见下表）
- 自动跑 **4 项隐私检测**，发现泄露时机器人切换姿势提醒
- 点开看完整 IP、城市、ISP、安全检测详情
- 切换 VPN / Wi-Fi 时立刻自动重新检测，不用等

---

## 🤖 四种状态

| 图标 | 状态 | 含义 |
|---|---|---|
| <img src="assets/icons/app/icon_ok_256.png" width="48" />      | **ok**       | 联网正常，且 4 项隐私检测全部通过（站立机器人） |
| <img src="assets/icons/app/icon_ok_risk_256.png" width="48" /> | **ok_risk**  | 联网正常，但至少 1 项隐私检测发现风险（坐姿机器人） |
| 🔄                                                              | **checking** | 正在检测网络 / 切换中（循环箭头） |
| ⚠️                                                              | **error**    | 网络异常，无法获取公网 IP（警告三角） |

> macOS 菜单栏：`ok` / `ok_risk` 用机器人 template（自动反色适配深 / 浅外观）；`checking` / `error` 用 SF Symbol（系统矢量图标，形状不会被颜色误导）。  
> Linux / Windows 托盘：把国家码画进图标，4 种状态用背景色区分（绿 / 橙 / 黄 / 红）。

---

## 🔒 隐私检测

NetBot 在每次拿到新 IP 时自动跑 4 项检测，结果在下拉菜单 **「🔒 安全检测」** 里展开。检测项分两档：

**🔐 关键（真实身份泄露 · 任一项失败会让图标切到坐姿）**

| 项 | 检测什么 |
|---|---|
| **DNS 泄露** | 你正在用的 DNS 解析器是否走 VPN —— 没走的话，本地 / ISP 的 DNS 服务器能看到你查询的每个域名。比对 *DNS resolver 出口国* vs *公网 IPv4 出口国* |
| **IPv6 泄露** | IPv6 流量是否也走 VPN —— 多数廉价机场只接管 IPv4，访问支持 IPv6 的网站时会 *绕过 VPN* 暴露真实地址。比对 *IPv6 echo 归属国* vs *公网 IPv4 出口国* |

**ℹ️ 提示（仅供参考 · 不影响图标状态）**

| 项 | 检测什么 |
|---|---|
| **IP 信誉** | 出口 IP 是否被标为 VPN / 代理 / Tor / 数据中心 —— 被标了不漏身份，但很多网站会加验证码或拒服务 |
| **地理一致性** | IP 国别 vs 系统时区 / locale 是否一致 —— 不一致时浏览器 Accept-Language + JS 时区会暴露"你其实在哪"。不漏身份，是"被识破在用代理"的问题 |

### 边界声明

这些是 **"客户端能检测的隐私泄露信号"**，不是 IDS / 入侵检测。NetBot **无法**回答以下问题：

- 是否有人在反向追踪你 → 需要网络嗅探设备
- 你的 VPN 服务商是否在记录访问 → 客户端无从验证
- 流量是否被中间人篡改 → 需要为每个目标做证书固定

### 数据流向

- **DNS / IPv6 / 地理一致性** —— 全部本地完成，不出本机
- **IP 信誉** —— 调用 [ipapi.is](https://ipapi.is) 匿名接口（1000 次/日免费额度），只发送公网 IP，不带其他信息

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

## 🔄 升级

- **macOS / Linux**：再跑一次同样的一键安装命令即可。脚本会自动退掉正在运行的旧版本、装新版、重启。
- **Windows**：托盘图标右键 → 退出，下载新 `NetBot.exe` 覆盖原来的位置 → 双击。

---

## 📜 License

[MIT](LICENSE)
