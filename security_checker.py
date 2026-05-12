"""
网络安全检测模块

四项检测：
  1. DNS leak       —— 用 Cloudflare 1.1.1.1 直连查 whoami 服务，得到出口 DNS resolver IP，
                       拿它的归属国 vs 公网 IP 的归属国比较
  2. IPv6 leak      —— 请求 IPv6-only 端点，看是否能拿到 IPv6 地址；
                       如果能拿到且不属于 VPN 端，说明 VPN 没接管 IPv6
  3. IP reputation  —— 调用 ipapi.is 匿名接口（免费 1000/日），看 IP 是否被标记 VPN/proxy/tor/datacenter
  4. Geo consistency—— 系统时区 / locale 与 IP 归属国比对，差距大就提示

设计：
  · 每项独立、可单独失败 —— 一项查不动不影响其它三项
  · 全部返回 {key, ok, label, detail}，UI 直接展示
  · 不抛异常（出错就 ok=True 且 detail="未能检测"，避免误报）
  · 所有 HTTP / DNS 都有 3 秒超时，不卡 UI
"""

from __future__ import annotations

import locale
import socket
import time
from datetime import datetime, timezone
from typing import Optional

import requests

# ============== 配置 ==============

REQUEST_TIMEOUT = 3
DNS_TIMEOUT = 2

# 用 Cloudflare 的 whoami DNS：通过你正在用的解析器查询时，
# 它会返回 *解析器自己的出口 IP*（不是你的）。这是检测 DNS 泄露的经典方法。
DNS_WHOAMI_NAME = "whoami.cloudflare"
DNS_WHOAMI_TYPE = "TXT"

# IPv6-only 端点。如果本机没启 IPv6 或 VPN 屏蔽了，这个请求会失败 —— 那就没泄露
IPV6_ECHO_ENDPOINTS = [
    "https://api6.ipify.org",
    "https://ipv6.icanhazip.com",
]

# ipapi.is 免费匿名接口
IPAPI_IS_ENDPOINT = "https://api.ipapi.is/?q={ip}"


# ============== 单项检测 ==============

def check_dns_leak(public_ip_country_iso2: str) -> dict:
    """
    比对：你正在用的 DNS 解析器出口在哪国 vs 你的公网 IP 在哪国。
    不一致 → DNS 没走 VPN，正在被本地/ISP DNS 看见你查啥。

    用 whoami.akamai.net 这个 trick 域名 —— 它的 A 记录返回你当前
    DNS resolver 的出口 IP。
    """
    try:
        resolver_ip = socket.gethostbyname("whoami.akamai.net")
    except (socket.gaierror, OSError) as e:
        return _skipped("dns_leak", "DNS 泄露", f"无法解析：{e}")

    # 私有 / 保留地址段 → VPN 客户端在本地拦截 DNS 转发进隧道，这是好事
    if _is_private_or_reserved(resolver_ip):
        return {
            "key": "dns_leak",
            "ok": True,
            "label": "DNS 泄露",
            "detail": f"DNS 被 VPN 客户端本地接管（resolver = {resolver_ip}）",
        }

    # 公网 resolver IP，比对国别
    resolver_country = _quick_country(resolver_ip)
    if resolver_country is None:
        return _skipped("dns_leak", "DNS 泄露", f"resolver {resolver_ip} 归属查询失败")

    public_country = (public_ip_country_iso2 or "").upper()
    if resolver_country.upper() != public_country:
        return {
            "key": "dns_leak",
            "ok": False,
            "label": "DNS 泄露",
            "detail": f"resolver 在 {resolver_country}，公网 IP 在 {public_country or '?'} —— DNS 没走 VPN",
        }
    return {
        "key": "dns_leak",
        "ok": True,
        "label": "DNS 泄露",
        "detail": f"resolver 与公网 IP 同在 {public_country}",
    }


def check_ipv6_leak() -> dict:
    """
    主动请求 IPv6-only 端点。
      · 拿到 IPv6 地址 → 本机有 IPv6 出口，但 VPN 通常只接管 IPv4 →
        访问支持 IPv6 的网站时会 *绕过 VPN* 直连，暴露真实 IPv6
      · 请求失败（连接拒绝 / 超时）→ 没有 IPv6 出口，没有泄露
    """
    for url in IPV6_ECHO_ENDPOINTS:
        try:
            resp = requests.get(url, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200:
                ipv6 = resp.text.strip()
                if ":" in ipv6:
                    return {
                        "key": "ipv6_leak",
                        "ok": False,
                        "label": "IPv6 泄露",
                        "detail": f"本机有 IPv6 出口 ({ipv6})，VPN 通常只走 IPv4，请在 VPN 客户端禁用 IPv6 或全局屏蔽",
                    }
        except requests.RequestException:
            continue

    # 全部失败 = 没有 IPv6 出口 = 安全
    return {
        "key": "ipv6_leak",
        "ok": True,
        "label": "IPv6 泄露",
        "detail": "无 IPv6 出口",
    }


def check_ip_reputation(ip: str) -> dict:
    """
    调 ipapi.is 看当前 IP 是否被标为 VPN / proxy / Tor / datacenter。
    被标了不代表不安全 —— 但很多网站会拒服务、风控加验证码。
    """
    try:
        resp = requests.get(IPAPI_IS_ENDPOINT.format(ip=ip), timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            return _skipped("ip_reputation", "IP 信誉", f"接口返回 {resp.status_code}")
        data = resp.json()
    except (requests.RequestException, ValueError) as e:
        return _skipped("ip_reputation", "IP 信誉", f"查询失败：{e}")

    flags = []
    is_vpn = bool(data.get("is_vpn"))
    is_proxy = bool(data.get("is_proxy"))
    is_tor = bool(data.get("is_tor"))
    is_dc = bool(data.get("is_datacenter"))
    is_abuser = bool(data.get("is_abuser"))

    if is_vpn:    flags.append("VPN")
    if is_proxy:  flags.append("代理")
    if is_tor:    flags.append("Tor")
    if is_dc:     flags.append("数据中心")
    if is_abuser: flags.append("滥用")

    if flags:
        return {
            "key": "ip_reputation",
            "ok": False,
            "label": "IP 信誉",
            "detail": "被标为：" + " / ".join(flags) + "（部分网站可能加验证码或拒服务）",
        }
    return {
        "key": "ip_reputation",
        "ok": True,
        "label": "IP 信誉",
        "detail": "未被标记为 VPN/代理/数据中心",
    }


def check_geo_consistency(public_ip_country_iso2: str) -> dict:
    """
    系统时区 / 系统 locale 与 IP 归属国是否一致。
    机场 VPN 用户常见情况：
      · 系统是 zh_CN.UTF-8 / Asia/Shanghai，但 IP 在 SG
      → 访问敏感网站时，浏览器 Accept-Language + JS 时区会暴露你"其实在中国"
    """
    public_country = (public_ip_country_iso2 or "").upper()
    if not public_country:
        return _skipped("geo_consistency", "地理一致性", "公网 IP 归属国未知")

    sys_tz = _system_timezone_name()
    sys_locale = _system_locale_country()

    tz_country = _tz_to_country(sys_tz)

    mismatches = []
    if tz_country and tz_country != public_country:
        mismatches.append(f"时区暗示 {tz_country}（{sys_tz}）")
    if sys_locale and sys_locale != public_country:
        mismatches.append(f"locale 是 {sys_locale}")

    if mismatches:
        return {
            "key": "geo_consistency",
            "ok": False,
            "label": "地理一致性",
            "detail": "IP 在 " + public_country + "，但 " + " / ".join(mismatches)
                      + " —— 网站可能识破代理",
        }
    return {
        "key": "geo_consistency",
        "ok": True,
        "label": "地理一致性",
        "detail": f"系统设置与 IP 归属一致（{public_country}）",
    }


# ============== 顶层入口 ==============

def run_all_checks(ip: str, country_iso2: str) -> list[dict]:
    """
    执行全部四项检测，返回列表。出错的项会被跳过（标 ok=True、detail=理由）。
    UI 直接遍历这个列表展示。
    """
    return [
        check_dns_leak(country_iso2),
        check_ipv6_leak(),
        check_ip_reputation(ip),
        check_geo_consistency(country_iso2),
    ]


def has_risk(results: list[dict]) -> bool:
    """任一项 ok=False 即视为有风险。"""
    return any(not r.get("ok", True) for r in results)


# ============== 工具函数 ==============

def _skipped(key: str, label: str, reason: str) -> dict:
    """检测无法完成时返回中性结果（不当成风险，避免误报）。"""
    return {"key": key, "ok": True, "label": label, "detail": f"未能检测（{reason}）"}


def _is_private_or_reserved(ip: str) -> bool:
    """判断是否在 RFC1918 / RFC6598 / loopback / link-local 等保留段。"""
    import ipaddress
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved


def _quick_country(ip: str) -> Optional[str]:
    """轻量查询 IP 国别 —— 复用 ipinfo.io 无 token 通道。"""
    try:
        resp = requests.get(f"https://ipinfo.io/{ip}/country", timeout=REQUEST_TIMEOUT)
        if resp.status_code == 200:
            return resp.text.strip().upper() or None
    except requests.RequestException:
        pass
    return None


def _system_timezone_name() -> Optional[str]:
    """
    读 IANA 时区名，例如 'Asia/Shanghai'。
    优先级：
      1. /etc/localtime 符号链接（macOS / Linux 标准做法）
      2. TZ 环境变量
      3. datetime tzinfo.key （Python 3.9+ zoneinfo 时可用）
      4. 时区缩写（最后兜底，可能歧义）
    """
    import os

    try:
        if os.path.islink("/etc/localtime"):
            target = os.readlink("/etc/localtime")
            # 典型路径：/var/db/timezone/zoneinfo/Asia/Shanghai
            #         或 ../usr/share/zoneinfo/Asia/Shanghai
            if "zoneinfo/" in target:
                return target.split("zoneinfo/", 1)[1]
    except OSError:
        pass

    tz_env = os.environ.get("TZ")
    if tz_env and "/" in tz_env:
        return tz_env

    try:
        tz = datetime.now(timezone.utc).astimezone().tzinfo
        return getattr(tz, "key", None) or str(tz)
    except Exception:
        return None


def _system_locale_country() -> Optional[str]:
    """读系统 locale 的国家段，例如 zh_CN -> CN。"""
    try:
        loc = locale.getlocale()[0]  # 例如 'zh_CN'
        if loc and "_" in loc:
            return loc.split("_", 1)[1].upper()
    except Exception:
        pass
    return None


# 常见 IANA 时区前缀 -> ISO2 国家码（够覆盖 90% 用户即可，不命中就跳过）
_TZ_PREFIX_TO_COUNTRY = {
    "Asia/Shanghai": "CN", "Asia/Chongqing": "CN", "Asia/Urumqi": "CN",
    "Asia/Hong_Kong": "HK", "Asia/Taipei": "TW",
    "Asia/Tokyo": "JP", "Asia/Seoul": "KR", "Asia/Singapore": "SG",
    "Asia/Bangkok": "TH", "Asia/Kuala_Lumpur": "MY", "Asia/Jakarta": "ID",
    "Asia/Manila": "PH", "Asia/Ho_Chi_Minh": "VN", "Asia/Kolkata": "IN",
    "Asia/Dubai": "AE", "Asia/Riyadh": "SA", "Asia/Jerusalem": "IL",
    "America/New_York": "US", "America/Chicago": "US", "America/Denver": "US",
    "America/Los_Angeles": "US", "America/Phoenix": "US", "America/Anchorage": "US",
    "America/Toronto": "CA", "America/Vancouver": "CA",
    "America/Mexico_City": "MX", "America/Sao_Paulo": "BR", "America/Buenos_Aires": "AR",
    "Europe/London": "GB", "Europe/Berlin": "DE", "Europe/Paris": "FR",
    "Europe/Amsterdam": "NL", "Europe/Madrid": "ES", "Europe/Rome": "IT",
    "Europe/Zurich": "CH", "Europe/Stockholm": "SE", "Europe/Oslo": "NO",
    "Europe/Helsinki": "FI", "Europe/Copenhagen": "DK", "Europe/Vienna": "AT",
    "Europe/Warsaw": "PL", "Europe/Moscow": "RU", "Europe/Istanbul": "TR",
    "Australia/Sydney": "AU", "Australia/Melbourne": "AU", "Pacific/Auckland": "NZ",
    "Africa/Johannesburg": "ZA",
}


def _tz_to_country(tz_name: Optional[str]) -> Optional[str]:
    """根据 IANA 时区名估计国家。命中表就返回，否则返回 None。"""
    if not tz_name:
        return None
    return _TZ_PREFIX_TO_COUNTRY.get(tz_name)
