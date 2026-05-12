"""
网络检测模块
负责：
  1. 获取当前公网 IP（轻量请求）
  2. 当 IP 发生变化时，查询归属地详情
  3. 本地缓存 IP -> 归属地 映射
  4. 监听 macOS 网络接口状态变化
"""

import os
import time
import socket
import threading
from typing import Optional, Callable

import requests
import psutil

# ============== 配置区（可自由修改） ==============

# 公网 IP 探测端点：返回纯文本 IP，体量极小
IP_ECHO_ENDPOINTS = [
    "https://ifconfig.me/ip",
    "https://api.ipify.org",
    "https://ipv4.icanhazip.com",
]

# 归属地查询端点（ipinfo.io 免费版无需 token）
IPINFO_ENDPOINT = "https://ipinfo.io/{ip}/json"

# 可选：从环境变量读取 ipinfo token（付费版本/更高额度）
IPINFO_TOKEN_ENV = "IPINFO_TOKEN"

# 网络请求超时（秒）
REQUEST_TIMEOUT = 5

# 默认轮询间隔（秒），由调用方控制
DEFAULT_POLL_INTERVAL = 30

# ============== 国家名 -> ISO3 简易映射 ==============
# ipinfo.io 返回的是 ISO2 国家码（如 "US"），菜单栏需要 ISO3（如 "USA"）
# 这里维护一个常见地区的映射表；未命中时直接回退到 ISO2
ISO2_TO_ISO3 = {
    "US": "USA", "CN": "CHN", "JP": "JPN", "SG": "SGP", "HK": "HKG",
    "TW": "TWN", "KR": "KOR", "GB": "GBR", "DE": "DEU", "FR": "FRA",
    "CA": "CAN", "AU": "AUS", "RU": "RUS", "IN": "IND", "BR": "BRA",
    "NL": "NLD", "IT": "ITA", "ES": "ESP", "CH": "CHE", "SE": "SWE",
    "NO": "NOR", "FI": "FIN", "DK": "DNK", "IE": "IRL", "BE": "BEL",
    "AT": "AUT", "PL": "POL", "TR": "TUR", "MX": "MEX", "AR": "ARG",
    "MY": "MYS", "TH": "THA", "VN": "VNM", "ID": "IDN", "PH": "PHL",
    "AE": "ARE", "SA": "SAU", "IL": "ISR", "ZA": "ZAF", "NZ": "NZL",
    "UA": "UKR", "CZ": "CZE", "PT": "PRT", "GR": "GRC", "RO": "ROU",
    "HU": "HUN", "IS": "ISL", "LU": "LUX",
}


def iso2_to_iso3(code: str) -> str:
    """把 ipinfo 返回的两位国家码转成三位 ISO3 缩写。"""
    if not code:
        return "---"
    return ISO2_TO_ISO3.get(code.upper(), code.upper())


class NetworkMonitor:
    """网络监控器：探测公网 IP、查询归属地、监听接口变化。"""

    def __init__(
        self,
        on_update: Callable[[dict], None],
        on_error: Callable[[str], None],
        on_checking: Callable[[], None],
        poll_interval: int = DEFAULT_POLL_INTERVAL,
    ):
        """
        :param on_update:   成功获取归属地后回调，传入 info 字典
        :param on_error:    出错时回调，传入错误消息
        :param on_checking: 正在检测时回调（用于切换“思考”图标）
        :param poll_interval: 轮询间隔（秒）
        """
        self.on_update = on_update
        self.on_error = on_error
        self.on_checking = on_checking
        self.poll_interval = poll_interval

        # 本地缓存：ip -> info dict（避免重复查询同一个 IP）
        self._ip_cache: dict[str, dict] = {}
        # 最近一次记录的公网 IP
        self._current_ip: Optional[str] = None
        # 最近一次记录的网络接口状态快照（用于检测变化）
        self._last_if_snapshot: Optional[dict] = None
        # 线程控制
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    # ---------- 对外接口 ----------

    def start(self):
        """启动后台轮询线程。"""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """停止后台线程。"""
        self._stop_event.set()

    def force_refresh(self):
        """立即强制刷新一次（不走缓存）。在 UI 线程触发即可。"""
        threading.Thread(target=self._tick, kwargs={"force": True}, daemon=True).start()

    # ---------- 主循环 ----------

    def _run_loop(self):
        """后台循环：定时探测 + 网络变化即时探测。"""
        # 启动时立刻探测一次
        self._tick(force=True)

        while not self._stop_event.is_set():
            # 拆分睡眠为小段，方便快速响应 stop 与网络变化事件
            slept = 0
            while slept < self.poll_interval and not self._stop_event.is_set():
                time.sleep(1)
                slept += 1
                # 每秒检查一次网络接口状态变化（开销极低）
                if self._network_interfaces_changed():
                    # 网络变化时立即跳出睡眠，触发强制检测
                    self._tick(force=True)
                    break
            else:
                # 正常超时：跑一次轮询
                if not self._stop_event.is_set():
                    self._tick(force=False)

    def _tick(self, force: bool = False):
        """一次完整的探测周期。"""
        # 通知 UI 正在检测
        try:
            self.on_checking()
        except Exception:
            pass

        # 第一步：获取公网 IP（轻量）
        ip = self._fetch_public_ip()
        if not ip:
            self._safe_error("无法获取公网 IP")
            return

        # 第二步：IP 没变且非强制刷新，则复用缓存
        if not force and ip == self._current_ip and ip in self._ip_cache:
            cached = self._ip_cache[ip]
            cached["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            self._safe_update(cached)
            return

        # 第三步：IP 变了或强制刷新，查询归属地
        info = self._fetch_ip_info(ip)
        if not info:
            self._safe_error("归属地查询失败")
            return

        self._current_ip = ip
        self._ip_cache[ip] = info
        self._safe_update(info)

    # ---------- 网络变化检测 ----------

    def _network_interfaces_changed(self) -> bool:
        """
        通过 psutil.net_if_stats 探测网络接口 up/down 变化。
        相比直接调用 SystemConfiguration，跨平台且无需 PyObjC。
        """
        try:
            stats = psutil.net_if_stats()
        except Exception:
            return False

        snapshot = {name: (s.isup, s.speed) for name, s in stats.items()}
        if self._last_if_snapshot is None:
            self._last_if_snapshot = snapshot
            return False
        changed = snapshot != self._last_if_snapshot
        self._last_if_snapshot = snapshot
        return changed

    # ---------- HTTP 请求 ----------

    def _fetch_public_ip(self) -> Optional[str]:
        """依次尝试多个 echo 端点，任一成功即返回。"""
        for url in IP_ECHO_ENDPOINTS:
            try:
                resp = requests.get(url, timeout=REQUEST_TIMEOUT)
                if resp.status_code == 200:
                    ip = resp.text.strip()
                    # 简单合法性校验
                    if self._looks_like_ip(ip):
                        return ip
            except (requests.RequestException, socket.error):
                continue
        return None

    def _fetch_ip_info(self, ip: str) -> Optional[dict]:
        """调用 ipinfo.io 获取归属地详情。"""
        url = IPINFO_ENDPOINT.format(ip=ip)
        headers = {"Accept": "application/json"}
        # 可选 token
        token = os.environ.get(IPINFO_TOKEN_ENV)
        params = {"token": token} if token else None

        try:
            resp = requests.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
            if resp.status_code != 200:
                return None
            data = resp.json()
        except (requests.RequestException, ValueError):
            return None

        country_iso2 = data.get("country", "")
        return {
            "ip": data.get("ip", ip),
            "country_iso2": country_iso2,
            "country_iso3": iso2_to_iso3(country_iso2),
            "country_name": COUNTRY_FULL_NAME.get(country_iso2.upper(), country_iso2 or "Unknown"),
            "city": data.get("city", ""),
            "region": data.get("region", ""),
            "org": data.get("org", ""),
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

    # ---------- 工具方法 ----------

    @staticmethod
    def _looks_like_ip(text: str) -> bool:
        """粗略判断字符串是否像 IPv4/IPv6 地址。"""
        if not text or len(text) > 64:
            return False
        try:
            socket.inet_aton(text)
            return True
        except OSError:
            pass
        # 尝试 IPv6
        try:
            socket.inet_pton(socket.AF_INET6, text)
            return True
        except (OSError, AttributeError):
            return False

    def _safe_update(self, info: dict):
        try:
            self.on_update(info)
        except Exception:
            pass

    def _safe_error(self, msg: str):
        try:
            self.on_error(msg)
        except Exception:
            pass


# ============== 国家全名映射（用于下拉菜单显示） ==============
COUNTRY_FULL_NAME = {
    "US": "United States", "CN": "China", "JP": "Japan", "SG": "Singapore",
    "HK": "Hong Kong", "TW": "Taiwan", "KR": "South Korea", "GB": "United Kingdom",
    "DE": "Germany", "FR": "France", "CA": "Canada", "AU": "Australia",
    "RU": "Russia", "IN": "India", "BR": "Brazil", "NL": "Netherlands",
    "IT": "Italy", "ES": "Spain", "CH": "Switzerland", "SE": "Sweden",
    "NO": "Norway", "FI": "Finland", "DK": "Denmark", "IE": "Ireland",
    "BE": "Belgium", "AT": "Austria", "PL": "Poland", "TR": "Turkey",
    "MX": "Mexico", "AR": "Argentina", "MY": "Malaysia", "TH": "Thailand",
    "VN": "Vietnam", "ID": "Indonesia", "PH": "Philippines", "AE": "UAE",
    "SA": "Saudi Arabia", "IL": "Israel", "ZA": "South Africa", "NZ": "New Zealand",
    "UA": "Ukraine", "CZ": "Czech Republic", "PT": "Portugal", "GR": "Greece",
    "RO": "Romania", "HU": "Hungary", "IS": "Iceland", "LU": "Luxembourg",
}
