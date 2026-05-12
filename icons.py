"""
图标模块（macOS 菜单栏）

四种状态：
  · ok       → 像素机器人站姿 template PNG（tray_ok_template.png）
  · ok_risk  → 像素机器人坐姿 / 躺姿 template PNG（tray_ok_risk_template.png）
               目前没出图：暂时回退到 ok 的站姿 + SF Symbol 警告角标合成方案
  · checking → SF Symbol  arrow.triangle.2.circlepath（旋转双箭头）
  · error    → SF Symbol  exclamationmark.triangle.fill（警告三角）
"""

import os
import shutil
import tempfile
from typing import Optional

from AppKit import NSImage, NSBitmapImageRep
from Foundation import NSData  # noqa: F401  # PyInstaller hooks 有时需要显式 import

# ============== SF Symbol 名称配置 ==============
SYMBOL_CHECKING = "arrow.triangle.2.circlepath"  # 检测中：刷新箭头
SYMBOL_ERROR = "exclamationmark.triangle.fill"   # 错误：警告三角

# ok / ok_risk 状态用打包好的 template PNG
_OK_TEMPLATE_PARTS = ("assets", "icons", "tray", "tray_ok_template.png")
_OK_RISK_TEMPLATE_PARTS = ("assets", "icons", "tray", "tray_ok_risk_template.png")

# ok_risk 还没出图时的兜底符号（被风险标记的机器人）
SYMBOL_OK_RISK = "exclamationmark.shield.fill"   # 盾牌带感叹号

# 菜单栏图标像素尺寸（菜单栏高度约 22pt，18 看着比较协调）
ICON_SIZE = 18

# NSBitmapImageFileType.png = 4
_NS_PNG_FILE_TYPE = 4


def _asset_path(*parts: str) -> str:
    """兼容 PyInstaller 冻结环境的资源路径。"""
    import sys
    base = getattr(sys, "_MEIPASS", None) or os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, *parts)


def _render_symbol_to_png(symbol_name: str, out_path: str, size: int = ICON_SIZE) -> bool:
    """把一个 SF Symbol 渲染成单色 PNG（保留透明度，可当 template 用）。"""
    image = NSImage.imageWithSystemSymbolName_accessibilityDescription_(symbol_name, None)
    if image is None:
        return False

    image.setSize_((size, size))
    image.setTemplate_(True)

    tiff_data = image.TIFFRepresentation()
    if tiff_data is None:
        return False
    rep = NSBitmapImageRep.imageRepWithData_(tiff_data)
    if rep is None:
        return False
    png_data = rep.representationUsingType_properties_(_NS_PNG_FILE_TYPE, None)
    if png_data is None:
        return False
    return bool(png_data.writeToFile_atomically_(out_path, True))


def _copy_asset(src: str, dst: str) -> bool:
    """把仓库内的 template PNG 复制到缓存目录，让所有图标路径风格一致。"""
    try:
        shutil.copyfile(src, dst)
        return True
    except OSError:
        return False


def prepare_icons() -> dict[str, Optional[str]]:
    """
    准备四个状态图标，返回 {state: png_path}。
    渲染失败时该 state 的值是 None，调用方应当处理。
    """
    cache_dir = os.path.join(tempfile.gettempdir(), "netbot_icons")
    os.makedirs(cache_dir, exist_ok=True)

    result: dict[str, Optional[str]] = {}

    # ok：从资产里拷贝出来
    ok_src = _asset_path(*_OK_TEMPLATE_PARTS)
    ok_dst = os.path.join(cache_dir, "ok.png")
    result["ok"] = ok_dst if os.path.exists(ok_src) and _copy_asset(ok_src, ok_dst) else None

    # ok_risk：优先用资产里的坐姿/躺姿 template，没有就用 SF Symbol 盾牌兜底
    ok_risk_src = _asset_path(*_OK_RISK_TEMPLATE_PARTS)
    ok_risk_dst = os.path.join(cache_dir, "ok_risk.png")
    if os.path.exists(ok_risk_src) and _copy_asset(ok_risk_src, ok_risk_dst):
        result["ok_risk"] = ok_risk_dst
    else:
        result["ok_risk"] = ok_risk_dst if _render_symbol_to_png(SYMBOL_OK_RISK, ok_risk_dst) else None

    # checking / error：现场渲染 SF Symbol
    for state, symbol in (("checking", SYMBOL_CHECKING), ("error", SYMBOL_ERROR)):
        out = os.path.join(cache_dir, f"{state}.png")
        result[state] = out if _render_symbol_to_png(symbol, out) else None

    return result
