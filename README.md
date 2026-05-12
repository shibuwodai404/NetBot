# NetBot

> A lightweight tray app that tells you which country your public IP is from, in real time.

一个轻量的跨平台菜单栏 / 系统托盘小工具，实时显示当前网络出口 IP 的归属国家。
适合代理 / VPN 用户随时确认「自己现在到底从哪里上网」。

支持 **🍎 macOS · 🐧 Linux · 🪟 Windows**，三平台均提供预编译产物。

---

## ✨ 功能

- 三字母国家码（`USA` / `CHN` / `JPN` / `SGP` ...）一眼可见
- 颜色状态：🟢 正常 · 🟡 检测中 / 切换中 · 🔴 异常
- 点击查看：完整 IP、国家 / 城市、ISP、最后更新时间
- 智能轮询，不暴力刷：
  - 每 30 秒只做一次轻量级公网 IP 探测（几十字节）
  - 仅当 IP 变化时才调用 ipinfo.io 查询归属地
  - 监听网卡 up/down 事件，变化时立刻探测
- API 失败不崩溃，自动切红色 + 下次周期重试

---

## 📦 下载安装

到本仓库的 **[Releases](../../releases)** 页下载对应平台的产物。三个平台并列、互不依赖：

### 🍎 macOS

| 项目 | 内容 |
|---|---|
| 下载 | `NetBot.dmg`（推荐） 或 `NetBot.zip` |
| 安装 | 双击 `.dmg` 挂载 → 把 `NetBot.app` 拖到 `Applications` |
| 界面 | 菜单栏左侧 SF Symbol 图标 + 右侧三字母国家码 |
| 首次打开 | 未签名，Gatekeeper 会拦截并谎称「文件已损坏」（其实没坏）。<br/>**最稳的修复**（终端跑一行）：<br/>`xattr -dr com.apple.quarantine /Applications/NetBot.app`<br/>跑完双击即可正常打开。<br/><br/>新版 macOS 上，「右键 → 打开」的旧办法对下载来的未签名 App 经常无效，弹窗里没有"仍要打开"按钮，必须用上面这条 `xattr` 命令。 |
| 系统要求 | macOS 11 Big Sur 及以上 |

### 🐧 Linux

| 项目 | 内容 |
|---|---|
| 下载 | `NetBot-linux-x86_64.tar.gz` |
| 安装 | `tar -xzf NetBot-linux-x86_64.tar.gz && mv NetBot ~/.local/bin/` |
| 启动 | `NetBot &` 或加到「自启动应用」 |
| 界面 | 系统托盘里 64×64 圆角彩色图标，三字母国家码画在图标内部 |
| 系统要求 | 桌面环境需支持 AppIndicator：<br/>`sudo apt install libayatana-appindicator3-1 gir1.2-ayatanaappindicator3-0.1`<br/>GNOME 用户需开启 [AppIndicator 扩展](https://extensions.gnome.org/extension/615/appindicator-support/) |

### 🪟 Windows

| 项目 | 内容 |
|---|---|
| 下载 | `NetBot-windows-x64.zip` |
| 安装 | 解压后双击 `NetBot.exe`（建议放固定目录，加入「启动」文件夹可开机自启） |
| 界面 | 任务栏托盘 64×64 圆角彩色图标，三字母国家码画在图标内部，悬停查看完整信息 |
| 首次打开 | 未签名，SmartScreen 会拦一下。点「更多信息」→「仍要运行」（一次性） |
| 系统要求 | Windows 10 及以上 |

---

## 🛠️ 从源码运行 / 打包

需要 Python 3.9+。三平台均通用：

```bash
python3 -m venv .venv

# macOS / Linux
source .venv/bin/activate
# Windows PowerShell
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
python main.py
```

`requirements.txt` 使用 PEP 508 平台标记，pip 会自动按当前 OS 选装依赖。

### 自己打包发布

三个平台各有独立打包脚本，**完全对等**，互不依赖：

| 平台 | 命令 | 产物 |
|---|---|---|
| 🍎 macOS | `./build_macos.sh` | `dist/NetBot.app` · `dist/NetBot.dmg` · `dist/NetBot.zip` |
| 🐧 Linux | `./build_linux.sh` | `dist/NetBot` · `dist/NetBot-linux-<arch>.tar.gz` |
| 🪟 Windows | `.\build_windows.ps1` | `dist\NetBot.exe` · `dist\NetBot-windows-x64.zip` |

打包脚本统一：清理 → 安装依赖 → PyInstaller → 后处理（DMG / tar / zip）。

### CI / 自动 Release

仓库自带 `.github/workflows/build.yml`，三平台 matrix 并行构建：

- **每次 push / PR** → 三平台 artifact 自动上传（GitHub Artifact 默认保留 90 天）
- **推 tag `v*`**（例如 `v0.1.0`）→ 自动创建 GitHub Release 并附 `.dmg / .zip / .tar.gz / .exe`

发布流程：
```bash
git tag v0.1.0
git push origin v0.1.0
```

---

## 🏗️ 架构

```
NetBot/
├── main.py                       # 入口分发器：按 sys.platform 选 UI 后端
├── network_monitor.py            # IP 检测 / 归属地查询 / 缓存（跨平台核心）
│
├── ui_macos.py                   # 🍎 macOS 后端（rumps）
├── icons.py                      #     · SF Symbols → PNG
│
├── ui_pystray.py                 # 🐧 Linux + 🪟 Windows 后端（pystray）
├── icons_pil.py                  #     · PIL 渲染带文字的图标
│
├── build_macos.sh                # 🍎 打包脚本
├── build_linux.sh                # 🐧 打包脚本
├── build_windows.ps1             # 🪟 打包脚本
│
├── .github/workflows/build.yml   # 三平台 CI / Release
├── requirements.txt
└── README.md
```

**核心设计**：`network_monitor.py` 是跨平台的，UI 层按平台分发。这样图标 / 渲染细节后续可以独立优化，不会互相影响。

**为什么 Win/Linux 把国家码画进图标？**
macOS 菜单栏支持「图标 + 文字」并列，Win/Linux 的托盘只能放一个 16×16 ~ 64×64 的图标，所以把 `USA` 三个字母直接渲染到图标里，是这俩平台唯一能「一眼看到国家」的办法。状态用背景色区分（绿 / 黄 / 红）。

---

## ⚙️ 配置项

### `main.py` / `ui_*.py`
- `POLL_INTERVAL`：轮询间隔（默认 30 秒）
- `NETBOT_UI` 环境变量：在 macOS 上设 `NETBOT_UI=pystray` 可强制切到跨平台后端，便于本地调试 Win/Linux 路径

### 🍎 `icons.py`
- `SYMBOL_OK / SYMBOL_ERROR / SYMBOL_CHECKING`：SF Symbol 名称（用 macOS 上的 SF Symbols.app 查）
- `ICON_SIZE`：图标像素尺寸

### 🐧🪟 `icons_pil.py`
- `STATE_COLORS`：三种状态的背景色（RGBA）
- `FONT_CANDIDATES`：字体回退列表（已涵盖三平台常见路径）
- `ICON_SIZE`：画布像素尺寸（默认 64）

### `network_monitor.py`
- `IP_ECHO_ENDPOINTS`：公网 IP 探测端点列表（默认 ifconfig.me / ipify / icanhazip）
- `IPINFO_ENDPOINT`：归属地查询端点
- `REQUEST_TIMEOUT`：网络请求超时（默认 5 秒）
- `IPINFO_TOKEN` 环境变量：可选的 ipinfo.io 付费 token（免费版每月 50k 请求够用）

---

## 🔐 关于签名

未签名的产物 100% 可用，只是首次打开会被 Gatekeeper / SmartScreen 拦一下，按"首次打开"指引操作即可。

如需「双击零摩擦」体验：
- 🍎 **macOS**：Apple Developer 账号（$99/年）+ `codesign` + `notarytool` 公证
- 🪟 **Windows**：代码签名证书（$100~400/年）+ `signtool`
- 🐧 **Linux**：通常不需要签名

可后续按需补这一步。

---

## 📜 License

[MIT](LICENSE)
