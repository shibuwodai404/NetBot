"""
macOS 平台 UI（rumps）
菜单栏左侧显示状态图标，右侧显示国家码文字；下拉菜单展示 IP / 地区 / ISP / 安全检测。
"""

import rumps

from network_monitor import NetworkMonitor
from icons import prepare_icons

# 轮询间隔（秒）
POLL_INTERVAL = 30

# 启动时显示的国家码占位
INITIAL_COUNTRY = "..."


class NetBotApp(rumps.App):
    """菜单栏应用主类。"""

    def __init__(self):
        # 先把四张状态 PNG 渲染好
        self._icons = prepare_icons()

        super().__init__(
            name="NetBot",
            title=INITIAL_COUNTRY,
            icon=self._icons.get("checking"),
            template=True,           # 模板图：自动适配深 / 浅菜单栏
            quit_button=None,        # 手动加退出项，控制排序
        )

        # 下拉菜单项
        self.item_ip = rumps.MenuItem("IP: ...")
        self.item_country = rumps.MenuItem("地区: ...")
        self.item_org = rumps.MenuItem("ISP: ...")
        self.item_updated = rumps.MenuItem("更新时间: ...")

        # 安全检测父项 + 4 个子项（先建好占位，后面填内容）
        self.item_security = rumps.MenuItem("🔒 安全检测：...")
        self._security_children = [rumps.MenuItem(f"_slot_{i}") for i in range(4)]
        for child in self._security_children:
            self.item_security.add(child)

        self.item_refresh = rumps.MenuItem("立即刷新", callback=self.on_refresh)
        self.item_quit = rumps.MenuItem("退出", callback=self.on_quit)

        self.menu = [
            self.item_ip,
            self.item_country,
            self.item_org,
            self.item_updated,
            None,
            self.item_security,
            None,
            self.item_refresh,
            None,
            self.item_quit,
        ]

        # 启动网络监控
        self.monitor = NetworkMonitor(
            on_update=self._handle_update,
            on_error=self._handle_error,
            on_checking=self._handle_checking,
            poll_interval=POLL_INTERVAL,
        )
        self.monitor.start()

    # ---------- 内部工具 ----------

    def _set_state_icon(self, state: str):
        path = self._icons.get(state)
        if path:
            self.icon = path

    def _update_security_menu(self, security: list[dict]):
        """根据 4 项检测结果刷新「🔒 安全检测」子菜单。"""
        if not security:
            self.item_security.title = "🔒 安全检测：—"
            for child in self._security_children:
                child.title = "—"
            return

        risks = [r for r in security if not r.get("ok", True)]
        if risks:
            self.item_security.title = f"🔒 安全检测：⚠️ {len(risks)} 项风险"
        else:
            self.item_security.title = "🔒 安全检测：✅ 全部通过"

        for i, child in enumerate(self._security_children):
            if i < len(security):
                r = security[i]
                mark = "✅" if r.get("ok") else "⚠️"
                child.title = f"{mark} {r['label']}：{r['detail']}"
            else:
                child.title = "—"

    # ---------- 监控回调 ----------

    def _handle_update(self, info: dict):
        iso3 = info.get("country_iso3", "---") or "---"
        state = info.get("state", "ok")
        self._set_state_icon(state)
        self.title = iso3

        self.item_ip.title = f"IP: {info.get('ip', '---')}"

        country = info.get("country_name") or "Unknown"
        city = info.get("city") or ""
        region = info.get("region") or ""
        loc_parts = [p for p in (city, region) if p]
        loc_str = f"{country} · {', '.join(loc_parts)}" if loc_parts else country
        self.item_country.title = f"地区: {loc_str}"

        self.item_org.title = f"ISP: {info.get('org') or '---'}"
        self.item_updated.title = f"更新时间: {info.get('updated_at', '---')}"

        self._update_security_menu(info.get("security") or [])

    def _handle_error(self, msg: str):
        self._set_state_icon("error")
        self.title = "---"
        self.item_updated.title = f"更新时间: {msg}"

    def _handle_checking(self):
        self._set_state_icon("checking")

    # ---------- 菜单点击 ----------

    def on_refresh(self, _sender):
        self.monitor.force_refresh()

    def on_quit(self, _sender):
        self.monitor.stop()
        rumps.quit_application()


def run_app():
    """对外入口：被 main.py 分发器调用。"""
    NetBotApp().run()
