"""
Windows / Linux 平台 UI（pystray + PIL）

由于 Win/Linux 托盘图标不支持像 macOS 那样在图标旁显示文字，
这里把三字母国家码直接画进图标，鼠标悬停可看完整信息。
"""

import pystray

from network_monitor import NetworkMonitor
from icons_pil import render_country_icon

# 轮询间隔（秒）
POLL_INTERVAL = 30


class NetBotTray:
    """跨平台托盘应用。"""

    def __init__(self):
        # 状态
        self._country = "..."
        self._state = "checking"
        self._info: dict = {}

        # pystray Icon：icon 用 PIL.Image，title 是 hover tooltip
        self._icon = pystray.Icon(
            name="NetBot",
            icon=render_country_icon(self._country, self._state),
            title=self._tooltip(),
            menu=self._build_menu(),
        )

        # 网络监控
        self._monitor = NetworkMonitor(
            on_update=self._handle_update,
            on_error=self._handle_error,
            on_checking=self._handle_checking,
            poll_interval=POLL_INTERVAL,
        )

    # ---------- 菜单构建（label 用 lambda 支持动态文案） ----------

    def _build_menu(self) -> pystray.Menu:
        # 安全检测子菜单：4 个槽位，按结果动态渲染
        security_submenu = pystray.Menu(
            pystray.MenuItem(lambda _i: self._security_line(0), None, enabled=False),
            pystray.MenuItem(lambda _i: self._security_line(1), None, enabled=False),
            pystray.MenuItem(lambda _i: self._security_line(2), None, enabled=False),
            pystray.MenuItem(lambda _i: self._security_line(3), None, enabled=False),
        )
        return pystray.Menu(
            pystray.MenuItem(lambda _i: f"IP: {self._info.get('ip', '...')}", None, enabled=False),
            pystray.MenuItem(lambda _i: f"地区: {self._format_location()}", None, enabled=False),
            pystray.MenuItem(lambda _i: f"ISP: {self._info.get('org') or '---'}", None, enabled=False),
            pystray.MenuItem(lambda _i: f"更新时间: {self._info.get('updated_at', '---')}", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(lambda _i: self._security_summary(), security_submenu),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("立即刷新", self._on_refresh),
            pystray.MenuItem("退出", self._on_quit),
        )

    def _security_list(self) -> list:
        return self._info.get("security") or []

    def _security_summary(self) -> str:
        results = self._security_list()
        if not results:
            return "🔒 安全检测：…"
        risks = [r for r in results if not r.get("ok", True)]
        return f"🔒 安全检测：⚠️ {len(risks)} 项风险" if risks else "🔒 安全检测：✅ 全部通过"

    def _security_line(self, idx: int) -> str:
        results = self._security_list()
        if idx >= len(results):
            return "—"
        r = results[idx]
        mark = "✅" if r.get("ok") else "⚠️"
        return f"{mark} {r['label']}：{r['detail']}"

    def _format_location(self) -> str:
        country = self._info.get("country_name") or "Unknown"
        city = self._info.get("city") or ""
        region = self._info.get("region") or ""
        loc_parts = [p for p in (city, region) if p]
        return f"{country} · {', '.join(loc_parts)}" if loc_parts else country

    def _tooltip(self) -> str:
        """hover 时显示的浮窗文字。"""
        ip = self._info.get("ip")
        if ip:
            return f"NetBot · {self._country} · {ip}"
        return f"NetBot · {self._country}"

    # ---------- 状态刷新 ----------

    def _refresh_icon(self):
        """同时更新图标 / tooltip / 菜单。"""
        try:
            self._icon.icon = render_country_icon(self._country, self._state)
            self._icon.title = self._tooltip()
            self._icon.update_menu()
        except Exception:
            # 后台线程访问 pystray，部分平台可能短暂抛错，吞掉即可
            pass

    # ---------- 监控回调 ----------

    def _handle_update(self, info: dict):
        self._info = info
        self._country = info.get("country_iso3", "---") or "---"
        self._state = info.get("state", "ok")
        self._refresh_icon()

    def _handle_error(self, msg: str):
        self._country = "---"
        self._state = "error"
        # 把错误消息塞进 updated_at 字段，下拉菜单可见
        self._info = {**self._info, "updated_at": msg}
        self._refresh_icon()

    def _handle_checking(self):
        self._state = "checking"
        self._refresh_icon()

    # ---------- 菜单点击 ----------

    def _on_refresh(self, _icon, _item):
        self._monitor.force_refresh()

    def _on_quit(self, icon, _item):
        self._monitor.stop()
        icon.stop()

    # ---------- 启动 ----------

    def run(self):
        self._monitor.start()
        self._icon.run()


def run_app():
    """对外入口：被 main.py 分发器调用。"""
    NetBotTray().run()
